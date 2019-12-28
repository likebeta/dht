function do_sugg(obj, form_id, form_input_id) {
    let count = $(obj).val().length;
    let auto_div = $("#search__autocomplete");
    if (count > 0) {
        $(form_id).addClass("has-text");
        $.ajax({
            cache: true,
            async: true,
            url: "https://suggestion.baidu.com/su?wd=" + $(obj).val(),
            dataType: "jsonp",          //指定服务器返回的数据类型
            jsonp: "cb",                //指定参数名称
            //jsonpCallback: "show_sugg",  //指定回调函数名称
            success: function (result) {
                if (result.s.length === 0) {
                    return;
                }
                result.s = result.s.slice(0, 8);
                let html = '';
                for (let i = 0; i < result.s.length; i++) {
                    html += '<div class="acp" tabindex="' + (i + 1) + '"><span class="t-normal">' + result.s[i] + '</span></div>'
                }
                let tempDiv = document.createElement("div");
                $(form_id).addClass('has-suggestions');
                auto_div.show();
                let newDIV = $(tempDiv).addClass('acp-wrap').html(html);
                let fake_acp = document.createElement("div");
                fake_acp = $(fake_acp).addClass('acp').attr('tabindex', '0').text($(obj).val());
                fake_acp.hide();
                auto_div.html(newDIV);
                newDIV.prepend(fake_acp);
                auto_div.show();
                auto_div.find('.acp').on({
                    mouseenter: function () {
                        $("div.acp").removeClass('acp--highlight');
                        $(this).addClass("acp--highlight");
                        $(this).click(function () {
                            $(form_input_id).val($(this).text());
                            auto_div.hide();
                            $(form_id).submit();
                        })
                    },
                    mouseleave: function () {
                        $("div.acp").removeClass('acp--highlight');
                    }
                });
            }
        });
    } else {
        $(form_id).removeClass("has-text").removeClass('has-suggestions');
        auto_div.hide();
    }
}

//方向键控制页面控件焦点移动
function keyDown(event, form_input_id) {
    let suggs = $("div.acp");                             //通过class属性值获取控件组合
    let this_sugg = $(".acp.acp--highlight");             //通过class属性值获取控件组合
    let focus = document.activeElement;                   //得到处于激活状态的控件
    let e = window.event || event;                        //获取事件
    let key = e.keyCode;                                  //得到按下的键盘Ascii码
    let target_input = $(form_input_id);                  //得到按下的键盘Ascii码
    let this_tabindex = $(this_sugg).attr('tabindex');
    let this_flag = 0;
    let last_flag = 0;
    if (typeof this_tabindex === typeof undefined || this_tabindex === false) {
        this_flag = 0;
    } else {
        this_flag = parseInt(this_tabindex);
    }
    let last_tabindex = $(suggs).last().attr('tabindex');
    if (typeof last_tabindex === typeof undefined || last_tabindex === false) {
        last_flag = 0;
    } else {
        last_flag = parseInt(last_tabindex);
    }
    switch (key) {
        case 38:                //向上键
            $(suggs).removeClass('acp--highlight');
            if (this_flag > 0 && this_flag <= last_flag) {
                $(suggs[this_flag - 1]).addClass('acp--highlight');
                if (this_flag > 0) {
                    target_input.val($(suggs[this_flag - 1]).text());
                }
            } else if (this_flag === 0) {
                $(suggs[last_flag]).addClass('acp--highlight');
                target_input.val($(suggs[last_flag]).text());
            } else {
                //hi
            }
            e.returnValue = false;
            break;
        case 40:                //向下键
            $(suggs).removeClass('acp--highlight');
            if (this_flag >= 0 && this_flag < last_flag) {
                $(suggs[this_flag + 1]).addClass('acp--highlight');
                target_input.val($(suggs[this_flag + 1]).text());
            } else {
                $(suggs[0]).addClass('acp--highlight');
                target_input.val($(suggs[0]).text());
            }
            break;
        case 13:                //回车键
            if (this_flag > 0) {
                target_input.val($(suggs[this_flag]).text());
            }
            break;
    }
}

function showCopyAlert(type, title) {
    Swal.fire({
        type: type,
        title: title,
        showConfirmButton: false,
        // target: document.querySelector("#links"),
        position: "center",
        // customContainerClass: 'position-absolute',
        timer: 1500
    })
}