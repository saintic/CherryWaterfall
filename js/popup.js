var version = "v1";
var accesskey_id = "accesskey_id";
var accesskey_secret = "accesskey_secret";
function _sign(params) {
    /*
        @params object: uri请求参数(包含除signature外的公共参数)
    */
    if( typeof(params)!="object" ) {
        console.error("params is not an object");
        return false;
    }
    // NO.1 参数排序
    var _my_sorted = Object.keys(params).sort();
    // NO.2 排序后拼接字符串
    var canonicalizedQueryString = '';
    for (var _i in _my_sorted) {
        canonicalizedQueryString += _my_sorted[_i] + '=' + params[_my_sorted[_i]] + '&';
    }
    canonicalizedQueryString += accesskey_secret;
    // NO.3 加密返回签名: signature
    return md5(canonicalizedQueryString).toUpperCase();
}
function make_url(params) {
    /*
        @params object: uri请求参数(不包含公共参数)
    */
    if( typeof(params)!="object" ) {
        console.debug("params is not an object, set {}");
        var params = {};
    }
    // 获取当前时间戳
    var timestamp = Math.round(new Date().getTime() / 1000 - 5).toString();
    // 设置公共参数
    var publicParams = { accesskey_id: accesskey_id, version: version, timestamp: timestamp };
    // 添加加公共参数
    for (var i in publicParams) {
        params[i] = publicParams[i];
    }
    var uri = ''
    for (var i in params) {
        uri += i + '=' + params[i] + '&';
    }
    uri += 'signature=' + _sign(params);
    //console.log(uri);
    return uri
}
$.ajax({
    url:'http://127.0.0.1:13141/api/?'+make_url({Action: "getOne"}),
    success:function(res){
        console.log(res);
        if (res.code==0) {
            $('#picView').html('<img src="'+res.data.imgUrl+'" width="'+res.data.width+'px" height="'+res.data.height+'px" max-width="800px" max-height="600px">');
        }
    }
});