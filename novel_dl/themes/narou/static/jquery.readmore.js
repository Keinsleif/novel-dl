/**
 * jquery.readmore - Substring long paragraphs and make expandable with "more" link
 * @date 7 July 2010
 * @author Jake Trent  http://www.jtsnake.com/
 * @version 1.1
 */
(function($){
	$.fn.readmore = function(settings){
		if(this.length == 0) return this;

		var opts = $.extend({}, $.fn.readmore.defaults, settings);

		this.each(function(){
			var replacedString = $(this).html().replace(/(\r\n|\r|\n)/g, '').replace(/<br( \/)*>/gi, '\n');

			$(this).data('opts', opts);
			if(replacedString.length > opts.substr_len){
				abridge($(this));
				linkage($(this));
			}

			function linkage(elem){
				elem.append(elem.data('opts').more_link);
				elem.children('.more').click(function(event){
					var dotsElement = $(this).siblings('span:not(.hidden)');
					var hiddenElement = $(this).siblings('span.hidden');
					dotsElement.remove();
					$(this).remove();
					hiddenElement.replaceWith(hiddenElement.html());
				});
			}

			function abridge(elem){
				var opts = elem.data('opts');
				var txt = replacedString;
				var len = opts.substr_len;
				var dots = '<span>' + opts.ellipses + '</span>';
				var shown = txt.substring(0, len).replace(/\n/g, '<br />\n') + dots;
				var hidden = '<span class="hidden" style="display:none;">' + txt.substring(len, txt.length).replace(/\n/g, '<br />\n') + '</span>';
				elem.html(shown + hidden);
			}
		});

		return this;
	};

	// デフォルト値を設定
	$.fn.readmore.defaults = {
		substr_len:	500,		// 最初に表示させる文字数
		ellipses:	'&#8230;',	// 省略記号
		more_link:	'<a href="javascript:void(0);" class="more" style="cursor:pointer;">&gt;&gt;続きを読む</a>'
	};
})(jQuery);

// DOM初期化完了時
$(function(){
	// マイページトップで使用
	// 自己紹介
	$('.prf_selfintroduction').readmore({
		substr_len:	100	// 表示させたい文字数
	});

	// 連載小説トップで使用
	// あらすじ
	$('#novel_ex').readmore({
		substr_len:	300	// 表示させたい文字数
	});
});
