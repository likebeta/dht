from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor, defer
from protocol import MySQLProtocol # One instance of this per actual connection to MySQL
import error
from twisted.python.failure import Failure
from twisted.python import log
import pprint

DEBUG = False

def _escape(query, args=None, text_factory=str): # XXX: Add Rob's suggestion for escaping
    # TODO: Turn %% into % so that you can do a real %s
    if args is None:
        return query
    escaped_args = []
    for arg in args:
        escaped_args.append("null" if arg is None else "'%s'" % text_factory(arg).replace("\\","\\\\").replace("'", "\\'"))
    parts = ("[%s]" % str(query)).split('%s') # Add square brackets to
                                              # guarantee that %s on the end or
                                              # beginning get a corresponding
                                              # split
    if len(escaped_args) + 1 != len(parts):
        raise TypeError, 'not enough arguments for MySQL format string %s | %s' % (str(query), str(args))
    # Pad args so that there are an equal number of args and query
    escaped_args.insert(0, '')
    if len(parts) != len(escaped_args):
        raise TypeError, 'INTERNAL ERROR'
    # Now interpolate and remove the square brackets
    return (''.join(x + y for x, y in zip(escaped_args, parts)))[1:-1]

class MySQLConnection(ReconnectingClientFactory):
    """
    Takes the responsibility for the reactor.connectTCP call away from the user.

    Lazily connects to MySQL only when a query is run and stays connected only
    for up to idle_timeout seconds.

    Handles reconnecting on disconnection if there are queries which have not
    yet had results delivered.

    When excuting a query, waits until query_timeout expires before giving up
    and reconnecting (assuming this MySQL connection has "gone dead"). If
    retry_on_error == True, attempts the query again once reconnected.  If not,
    returns a Failure to the user's deferred.

    Also accepts a list of error strings from MySQL which should be considered
    temporary local failures, which should trigger a reconnect-and-retry rather
    than throwing the failure up to the user. These may be application-specific.

    Note that this and MySQLProtocol both serialise database access, so if you
    try to execute multiple queries in parallel, you will have to wait for one
    to finish before the next one starts. A ConnectionPool inspired by
    http://hg.rpath.com/rmake/file/0f76170d71b7/rmake/lib/dbpool.py is coming
    soon to solve this problem (thanks gxti).
    """

    protocol = MySQLProtocol

    def disconnect(self):
        """
        Close the connection and kill all the reconnection attempts
        """
        self.stopTrying()
        self.stateTransition(state='disconnecting')
        if self.client:
            # Do some clean-up
            self.client.setTimeout(None)
            self.client.transport.loseConnection()

    def __init__(self, hostname, username, password, database=None,
                 connect_timeout=None, query_timeout=None, idle_timeout=None,
                 retry_on_error=False, temporary_error_strings=[], port=3306,
                 pool=None, autoRepair=False, text_factory=str):

        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.connect_timeout = connect_timeout
        self.query_timeout = query_timeout
        self.idle_timeout = idle_timeout
        self.retry_on_error = retry_on_error
        self.temporary_error_strings = temporary_error_strings
        self.deferred = defer.Deferred() # This gets fired when we have a new
                                         # client which just got connected
        self._current_selected_db = None
        self._autoRepair = autoRepair

        self.state = 'disconnected'
        self.client = None # Will become an instance of MySQLProtocol
                           # precisely when we have a live connection

        self.pool = pool

        # Attributes relating to the queue
        self._pending_operations = []
        self._current_operation = None
        self._current_operation_dfr = None
        self._current_user_dfr = None

        # Set when we get disconnected, so that we know to attempt
        # a retry of a failed operation
        self._error_condition = False
        self.text_factory=text_factory

    def _handleIncomingRequest(self, name, fn, arg0, arg1):
        """
        A handler for all new requests, gets parameterised by
        runQuery, selectDb and runOperation
        """
        # We have some new work to do, in case we get disconnected, we want to try
        # reconnecting again now.
        self.continueTrying = 1
        user_dfr = defer.Deferred()
        self._pending_operations.append((user_dfr, fn, arg0, arg1))
        self._checkOperations()
        if DEBUG:
            print "Appending %s \"%s\" with args %s which is due to fire back on new user deferred %s" % (name, arg0, arg1, user_dfr)
        return user_dfr

    def runQuery(self, query, query_args=None):
        return self._handleIncomingRequest('query', self._doQuery, query, query_args)

    def fetchone(self, query, query_args=None):
        # XXX DANGER WILL ROBINSON! DANGER!
        # This method does not conform to PEP-249. It returns a single scalar
        # value of the first result in the first row, or None. PEP-249 expects
        # this method to return an entire row or None.
        d = self.runQuery(query, query_args)
        d.addCallback(self._fetchoneHandleResult)
        return d

    def _fetchoneHandleResult(self, result):
        if result == []:
            result = None
        if result:
            result = result[0][0]
        return result

    def runOperation(self, query, query_args=None):
        return self._handleIncomingRequest('operation', self._doOperation, query, query_args)

    def selectDb(self, db):
        self.database = db
        return self._handleIncomingRequest('selectDb', self._doSelectDb, db, None)

    def _executeCurrentOperation(self):
        # Actually execute it, operation_dfr will fire when the database returns
        user_dfr, func, query, query_args = self._current_operation

        if DEBUG:
            print "Setting current operation to %s" % str(self._current_operation)
            print "About to run %s(%s, %s) and fire back on %s" % (str(func), str(query), str(query_args), str(user_dfr))

        self._current_user_dfr = user_dfr
        operation_dfr = func(query, query_args)
        # Store a reference to the current operation (there's gonna be only one running at a time)
        self._current_operation_dfr = operation_dfr

        operation_dfr.addBoth(self._doneQuery)

        # Jump back into the game when that operation completes (done_query_error returns none
        # so the callback, not errback gets called)
        operation_dfr.addBoth(self._checkOperations)

    def _retryOperation(self):
        if DEBUG:
            print "Running retryOperation on current operation %s" % str(self._current_operation)
        if not self._current_operation:
            # Oh, we weren't doing anything
            return
        self._executeCurrentOperation()

    @defer.inlineCallbacks
    def _doneQuery(self, data):
        # The query deferred has fired
        if self._current_user_dfr:
            if isinstance(data, Failure):
                if data.check(error.MySQLError):
                    if data.value.args[0] in self.temporary_error_strings:
                        print "CRITICAL: Caught '%s', reconnecting and retrying" % (data.value.args[0])
                        self.client.transport.loseConnection()
                        return
                    """
                    Incorrect key file for table './autorepair/mailaliases.MYI'; try to repair it", 126, 'HY000'
                    Table './hybridcluster/filesystem_modification_counts' is marked as crashed and last (automatic?) repair failed", 144, 'HY000'
                    """
                    error_string = data.value.args[0]
                    keyCorruptionPrefix = 'Incorrect key file for table \'./'
                    start = None
                    if error_string.startswith(keyCorruptionPrefix) and self._autoRepair:
                        start = len(keyCorruptionPrefix)
                    elif "is marked as crashed and last (automatic?) repair failed" in error_string and self._autoRepair:
                        start = len("Table \'./")
                    if start:
                        dbfile = error_string[start:error_string.find("'", start)]
                        table = dbfile.rsplit('/', 1)[1].rsplit('.', 1)[0]
                        repair = "repair table " + table
                        log.msg(
                            channel="autorepair",
                            msgs=[error_string, "\n\tabout to repair", repr(repair)])
                        result = yield self.client.query(repair)
                        log.msg(
                            channel="autorepair",
                            msgs=["repair completed", repr(result)])
                        self._executeCurrentOperation()
                        return

                    if data.value.args[0] in self.temporary_error_strings:
                        print "CRITICAL: Caught '%s', reconnecting and retrying" % (data.value.args[0])
                        self.client.transport.loseConnection()
                        return
                if DEBUG:
                    print "Query failed with error %s, errback firing back on %s" % (data, self._current_user_dfr)
                # XXX: If this an errback due to MySQL closing the connection,
                # and we are retry_on_true, and so we have set
                # _error_condition,  shouldn't we mask the failure?
                self._current_user_dfr.errback(data)
            else:
                if DEBUG:
                    print "Query is done with result %s, firing back on %s" % (data, self._current_user_dfr)
                self._current_user_dfr.callback(data)
                if self.pool:
                    self.pool._doneQuery(self)
            self._current_user_dfr = None
        else:
            print "CRITICAL WARNING! Current user deferred was None when a query fired back with %s - there should always be a user deferred to fire the response to..." % data
            raise Exception("txMySQL internal inconsistency")
        self._error_condition = False
        self._current_operation = None
        self._current_operation_dfr = None
        # If that was a failure, the buck stops here, returning None instead of the failure stops it propogating

    def _checkOperations(self, _ign=None):
        """
        Takes one thing off the queue and runs it, if we can.  (i.e. if there
        is anything to run, and we're not waiting on a query to fire back to
        the user right now, i.e. current user deferred exists)
        """
        if DEBUG:
            print "Running checkOperations on the current queue of length %s while current operation is %s" % (str(len(self._pending_operations)), str(self._current_operation))
        #print "Got to _checkOperations"

        if self._pending_operations and not self._current_user_dfr:
            # Store its parameters in case we need to run it again
            self._current_operation = self._pending_operations.pop(0)
            self._executeCurrentOperation()

        return _ign

    def stateTransition(self, data=None, state='disconnected', reason=None):
        new_state = state
        old_state = self.state

        if new_state == old_state:
            # Not a transition, heh
            return

        if DEBUG:
            print "Transition from %s to %s" % (self.state, new_state)

        self.state = new_state

        # connected => not connected
        if old_state == 'connected' and new_state != 'connected':
            if DEBUG:
                print "We are disconnecting..."
            # We have just lost a connection, if we're in the middle of
            # something, send an errback, unless we're going to retry
            # on reconnect, in which case do nothing
            if not self.retry_on_error and self._current_operation:
                if DEBUG:
                    print "Not retrying on error, current user deferred %s about to get failure %s" % (self._current_user_dfr, reason)
                if self._current_user_dfr and not self._current_user_dfr.called:
                    if DEBUG:
                        print "Current user deferred exists and has not been called yet, running errback on deferred %s about to get failure %s" % (self._current_user_dfr, reason)
                    self._current_user_dfr.errback(reason)
                    self._current_user_dfr = None
                    self._current_operation = None
                    self._current_operation_dfr = None
                else:
                    if DEBUG:
                        print "Current user deferred has already been fired in error handler, not doing anything"

        # not connected => connected
        if old_state != 'connected' and new_state == 'connected':
            if DEBUG:
                print "We are connected..."
            # We have just made a new connection, if we were in the middle of
            # something when we got disconnected and we want to retry it, retry
            # it now
            if self._current_operation and self._error_condition:
                if self.retry_on_error:
                    print "Would have run retry here... %r" % (reason,)
                    if DEBUG:
                        print "Retrying on error %s, with current operation %s" % (str(reason), str(self._current_operation))
                    # Retry the current operation
                    if not (self.state == 'connecting' and self._error_condition and self.retry_on_error):
                        if DEBUG:
                            print "Not running the query now, because the reconnection handler will handle it"
                        self._retryOperation()

                else:
                    if DEBUG:
                        print "Not retrying on error, connection made, nothing to do."

            else:
                # We may have something in our queue which was waiting until we became connected
                if DEBUG:
                    print "Connected, check whether we have any operations to perform"
                self._checkOperations()

        return data

    def _handleConnectionError(self, reason, is_failed):
        # This may have been caused by TimeoutMixing disconnecting us.
        # TODO: If there's no current operation and no pending operations, don't both reconnecting
        # Use: self.stopTrying() and self.startTrying()?
        if DEBUG:
            print "Discarding client", self.client
        self.client = None
        if self._pending_operations or self._current_operation:
            if not is_failed:
                # On connectionFailed, rather than connectionLost, we will never have
                # started trying to execute the query yet, because we didn't get a connection
                # So only set _error_condition if it was a connectionLost, because it results
                # in behaviour which expects a current_operation
                self._error_condition = True
            if self.state != 'disconnecting':
                self.stateTransition(state='connecting', reason=reason)
        else:
            self.continueTrying = 0
            self.stateTransition(state='disconnected')

    def clientConnectionFailed(self, connector, reason):
        if DEBUG:
            print "Got clientConnectionFailed for reason %s" % str(reason)
        self._handleConnectionError(reason, is_failed=True)
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def clientConnectionLost(self, connector, reason):
        if DEBUG:
            print "Got clientConnectionLost for reason %s" % str(reason)
        self._handleConnectionError(reason, is_failed=False)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    @defer.inlineCallbacks
    def _begin(self):
        if self.state == 'disconnected':
            if DEBUG:
                print "Connecting after being disconnected, with connection timeout %s" % self.connect_timeout
            self.stateTransition(state='connecting')
            # TODO: Use UNIX socket if string is "localhost"
            reactor.connectTCP(self.hostname, self.port, self, timeout=self.connect_timeout)
            if DEBUG:
                print "(1) Yielding on a successful connection, deferred is %s" % self.deferred
            yield self.deferred # will set self.client
            if DEBUG:
                print "Yielding on a successful ready deferred which is", self.client.ready_deferred
            yield self.client.ready_deferred
        elif self.state == 'connecting':
            if DEBUG:
                print "(2) Yielding on a successful connection, deferred is %s" % self.deferred
            yield self.deferred
            if DEBUG:
                print "Yielding on a successful ready deferred"
            yield self.client.ready_deferred
        elif self.state == 'connected':
            if DEBUG:
                print "Already connected when a query was attempted, well that was easy"
            pass

    def buildProtocol(self, addr):
        if DEBUG:
            print "Building a new MySQLProtocol instance for connection to %s, attempting to connect, using idle timeout %s" % (addr, self.idle_timeout)
        #print "Running buildprotocol for %s" % addr
        p = self.protocol(self.username, self.password, self.database,
                idle_timeout=self.idle_timeout)
        p.factory = self
        self.client = p
        if DEBUG:
            print "New client is", self.client
        #print self.client.ready_deferred
        self.deferred.callback(self.client)
        self.deferred = defer.Deferred()
        def when_connected(data):
            if DEBUG:
                print "Connection just successfully made, and MySQL handshake/auth completed. About to transition to connected... (got data)", data
            self.stateTransition(state='connected')
            return data
        self.client.ready_deferred.addCallback(when_connected)
        def checkError(failure):
            if failure.check(error.MySQLError):
                if failure.value.args[0] in self.temporary_error_strings:
                    print "CRITICAL: Caught '%s', reconnecting and retrying" % (failure.value.args[0])
                    self.client.transport.loseConnection()
                    return # Terminate errback chain
            return failure
        if DEBUG:
            print " *** Attaching checkError to client.ready_deferred", self.client.ready_deferred
            print "current ready_deferred callbacks are"
            pprint.pprint(self.client.ready_deferred.callbacks)
        self.client.ready_deferred.addErrback(checkError)
        self.resetDelay()
        return p

    @defer.inlineCallbacks
    def _doQuery(self, query, query_args=None): # TODO query_args
        if DEBUG:
            print "Attempting an actual query \"%s\"" % _escape(query, query_args,self.text_factory)
        yield self._begin()
        if DEBUG:
            print "Finished issuing query, fetching all results"
        result = yield self.client.fetchall(_escape(query, query_args,self.text_factory))
        if DEBUG:
            print "Fetched %d results" % (len(result),)
        defer.returnValue(result)

    @defer.inlineCallbacks
    def _doOperation(self, query, query_args=None): # TODO query_args
        if DEBUG:
            print "Attempting an actual operation \"%s\"" % _escape(query, query_args,self.text_factory)
        yield self._begin()
        result = yield self.client.query(_escape(query, query_args,self.text_factory))
        defer.returnValue(result)

    @defer.inlineCallbacks
    def _doSelectDb(self, db, ignored):
        if DEBUG:
            print "Attempting an actual selectDb \"%s\"" % db
        yield self._begin()
        yield self.client.select_db(db)


class DeferredConnection:
    def __init__(self, pool):
        self._pool = pool
        self._deferred = defer.Deferred()
        self._deferred.addCallback(self._useConnection)

    def _useConnection(self, conn):
        return conn

    def runQuery(self, query, query_args=None):
        def _runQuery(c):
            return c.runQuery(query, query_args)
        self._deferred.addCallback(_runQuery)
        return self._deferred

    def runOperation(self, query, query_args=None):
        def _runOperation(c):
            return c.runOperation(query, query_args)
        self._deferred.addCallback(_runOperation)
        return self._deferred

    def selectDb(self, db):
        self._deferred.addCallback(lambda conn: conn.selectDb(db))
        return self._deferred

class ConnectionPool:
    """
    Represents a pool of connections to MySQL.
    """

    def __init__(self, hostname=None, username=None, password=None,
                 database=None,
                 num_connections=5, connect_timeout=None,
                 query_timeout=None, idle_timeout=None, retry_on_error=False,
                 temporary_error_strings=[], port=3306):
        # Connections in the pool that can be used to run queries
        self._unused_connections = []

        # Deferred connections whose execution is postponed until a
        # database connection becomes available.
        self._deferred_connections = []

        for i in xrange(0, num_connections):
            conn = MySQLConnection(hostname, username, password, database,
                                   connect_timeout, query_timeout,
                                   idle_timeout, retry_on_error,
                                   temporary_error_strings, port,
                                   self)
            self._unused_connections.append(conn)

    def _doneQuery(self, conn):
        """Called when a connection becomes available."""
        if self._deferred_connections:
            # If we have deferred connections, pick up the oldest one and
            # run it on the newly available connection.
            defconn = self._deferred_connections.pop(0)
            defconn._deferred.callback(conn)
        else:
            # Otherwise just return the connection in the list of
            # available connections.
            self._unused_connections.append(conn)

    def _getConnection(self):
        if self._unused_connections:
            # If we have available connections return one
            conn = self._unused_connections.pop()
            return conn
        else:
            # Otherwise create a deferred connection which will be
            # executed when a connection from the pool becomes
            # available.
            defconn = DeferredConnection(self)
            self._deferred_connections.append(defconn)
            return defconn

    def runQuery(self, query, query_args=None):
        conn = self._getConnection()
        #return conn.runQuery(query, query_args)
        def err_back(ex):
            self._unused_connections.append(conn)
            raise ex
        d = conn.runQuery(query, query_args)
        d.addErrback(err_back)
        return d

    def runOperation(self, query, query_args=None):
        conn = self._getConnection()
        #return conn.runOperation(query, query_args)
        def err_back(ex):
            self._unused_connections.append(conn)
            raise ex
        d = conn.runOperation(query, query_args)
        d.addErrback(err_back)
        return d

    def selectDb(self, db):
        conn = self._getConnection()
        return conn.selectDb(db)
