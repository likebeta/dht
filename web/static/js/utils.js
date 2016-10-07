$ = window.$
$.cookie = {
    get: function(b) {
        var a = document.cookie.match(new RegExp("(^| )" + b + "=([^;]*)(;|$)"));
        return !a ? "" : decodeURIComponent(a[2])
    },
    set: function(c, e, d, f, a) {
        var b = new Date();
        if (a) {
            b.setTime(b.getTime() + 3600000 * a);
            document.cookie = c + "=" + e + "; expires=" + b.toGMTString() + "; path=" + (f ? f : "/") + "; " + (d ? ("domain=" + d + ";") : "")
        } else {
            document.cookie = c + "=" + e + "; path=" + (f ? f : "/") + "; " + (d ? ("domain=" + d + ";") : "")
        }
    },
    del: function(a, b, c) {
        document.cookie = a + "=; expires=Mon, 26 Jul 1997 05:00:00 GMT; path=" + (c ? c : "/") + "; " + (b ? ("domain=" + b + ";") : "")
    },
};
$.http = {
    jsonp: function(a) {
        var b = document.createElement("script");
        b.src = a;
        document.getElementsByTagName("head")[0].appendChild(b)
    },
    loadScript: function(c, d, b) {
        var a = document.createElement("script");
        a.onload = a.onreadystatechange = function() {
            if (!this.readyState || this.readyState === "loaded" || this.readyState === "complete") {
                if (typeof d == "function") {
                    d()
                }
                a.onload = a.onreadystatechange = null ;
                if (a.parentNode) {
                    a.parentNode.removeChild(a)
                }
            }
        }
        ;
        a.src = c;
        document.getElementsByTagName("head")[0].appendChild(a)
    },
    preload: function(a) {
        var b = document.createElement("img");
        b.src = a;
        b = null
    }
};
$.winName = {
    set: function(c, a) {
        var b = window.name || "";
        if (b.match(new RegExp(";" + c + "=([^;]*)(;|$)"))) {
            window.name = b.replace(new RegExp(";" + c + "=([^;]*)"), ";" + c + "=" + a)
        } else {
            window.name = b + ";" + c + "=" + a
        }
    },
    get: function(c) {
        var b = window.name || "";
        var a = b.match(new RegExp(";" + c + "=([^;]*)(;|$)"));
        return a ? a[1] : ""
    },
    clear: function(b) {
        var a = window.name || "";
        window.name = a.replace(new RegExp(";" + b + "=([^;]*)"), "")
    }
};
$.localStorage = {
    isSurport: function() {
        try {
            return window.localStorage ? true : false
        } catch (a) {
            return false
        }
    },
    get: function(b) {
        var a = "";
        try {
            a = window.localStorage.getItem(b)
        } catch (c) {
            a = ""
        }
        return a
    },
    set: function(a, b) {
        try {
            window.localStorage.setItem(a, b)
        } catch (c) {}
    },
    remove: function(a) {
        try {
            window.localStorage.removeItem(a)
        } catch (b) {}
    }
};
$.str = (function() {
    var htmlDecodeDict = {
        quot: '"',
        lt: "<",
        gt: ">",
        amp: "&",
        nbsp: " ",
        "#34": '"',
        "#60": "<",
        "#62": ">",
        "#38": "&",
        "#160": " "
    };
    var htmlEncodeDict = {
        '"': "#34",
        "<": "#60",
        ">": "#62",
        "&": "#38",
        " ": "#160"
    };
    return {
        decodeHtml: function(s) {
            s += "";
            return s.replace(/&(quot|lt|gt|amp|nbsp);/ig, function(all, key) {
                return htmlDecodeDict[key]
            }).replace(/&#u([a-f\d]{4});/ig, function(all, hex) {
                return String.fromCharCode(parseInt("0x" + hex))
            }).replace(/&#(\d+);/ig, function(all, number) {
                return String.fromCharCode(+number)
            })
        },
        encodeHtml: function(s) {
            s += "";
            return s.replace(/["<>& ]/g, function(all) {
                return "&" + htmlEncodeDict[all] + ";"
            })
        },
        trim: function(str) {
            str += "";
            var str = str.replace(/^\s+/, "")
              , ws = /\s/
              , end = str.length;
            while (ws.test(str.charAt(--end))) {}
            return str.slice(0, end + 1)
        },
        uin2hex: function(str) {
            var maxLength = 16;
            str = parseInt(str);
            var hex = str.toString(16);
            var len = hex.length;
            for (var i = len; i < maxLength; i++) {
                hex = "0" + hex
            }
            var arr = [];
            for (var j = 0; j < maxLength; j += 2) {
                arr.push("\\x" + hex.substr(j, 2))
            }
            var result = arr.join("");
            eval('result="' + result + '"');
            return result
        },
        bin2String: function(a) {
            var arr = [];
            for (var i = 0, len = a.length; i < len; i++) {
                var temp = a.charCodeAt(i).toString(16);
                if (temp.length == 1) {
                    temp = "0" + temp
                }
                arr.push(temp)
            }
            arr = "0x" + arr.join("");
            arr = parseInt(arr, 16);
            return arr
        },
        utf8ToUincode: function(s) {
            var result = "";
            try {
                var length = s.length;
                var arr = [];
                for (i = 0; i < length; i += 2) {
                    arr.push("%" + s.substr(i, 2))
                }
                result = decodeURIComponent(arr.join(""));
                result = $.str.decodeHtml(result)
            } catch (e) {
                result = ""
            }
            return result
        },
        json2str: function(obj) {
            var result = "";
            if (typeof JSON != "undefined") {
                result = JSON.stringify(obj)
            } else {
                var arr = [];
                for (var i in obj) {
                    arr.push("'" + i + "':'" + obj[i] + "'")
                }
                result = "{" + arr.join(",") + "}"
            }
            return result
        },
        time33: function(str) {
            var hash = 0;
            for (var i = 0, length = str.length; i < length; i++) {
                hash = hash * 33 + str.charCodeAt(i)
            }
            return hash % 4294967296
        },
        hash33: function(str) {
            var hash = 0;
            for (var i = 0, length = str.length; i < length; ++i) {
                hash += (hash << 5) + str.charCodeAt(i)
            }
            return hash & 2147483647
        }
    }
})();
$.check = {
    isHttps: function() {
        return document.location.protocol == "https:"
    },
    isSsl: function() {
        var a = document.location.host;
        return /^ssl./i.test(a)
    },
    isIpad: function() {
        var a = navigator.userAgent.toLowerCase();
        return /ipad/i.test(a)
    },
    isQQ: function(a) {
        return /^[1-9]{1}\d{4,9}$/.test(a)
    },
    isNick: function(a) {
        return /^[a-zA-Z]{1}([a-zA-Z0-9]|[-_]){0,19}$/.test(a)
    },
    isName: function(a) {
        if (a == "<请输入帐号>") {
            return false
        }
        return /[\u4E00-\u9FA5]{1,8}/.test(a)
    },
    isPhone: function(a) {
        return /^(?:86|886|)1\d{10}\s*$/.test(a)
    },
    isDXPhone: function(a) {
        return /^(?:86|886|)1(?:33|53|80|81|89)\d{8}$/.test(a)
    },
    isSeaPhone: function(a) {
        return /^(00)?(?:852|853|886(0)?\d{1})\d{8}$/.test(a)
    },
    isMail: function(a) {
        return /^\w+((-\w+)|(\.\w+))*\@[A-Za-z0-9]+((\.|-)[A-Za-z0-9]+)*\.[A-Za-z0-9]+$/.test(a)
    },
    isPassword: function(a) {
        return a && a.length >= 16
    },
    isForeignPhone: function(a) {
        return /^00\d{7,}/.test(a)
    },
};
function checkMobile() {
    var ua = navigator.userAgent;
    if (ua) {
        ua = ua.toLowerCase();
        var ignoreUa = ['ip', 'android', 'uc', 'phone', 'pad', 'bot', 'spider', 'slurp'];
        for (var i = 0; i < ignoreUa.length; i++) {
            if (ua.indexOf(ignoreUa[i]) > -1)
                return true;
        }
    }
    return window.screen.width < 1024;
}
var isMobile = checkMobile();
function addVisitCount() {
    var visitCount = $.cookie.get("visitCount")
    visitCount++;
    $.cookie.set("visitCount", visitCount, "", "", 5)
}
function rightAd() {
    if ((!isMobile) && (typeof (rightAds) != 'undefined')) {
        var index = generateRandom(0, rightAds.length)
        document.writeln(rightAds[index]);
    }
}
function generateRandom(min, max) {
    return Math.floor(Math.random() * (max - min) + min);
}
addVisitCount();
