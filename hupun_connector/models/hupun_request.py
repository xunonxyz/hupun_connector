# -*- coding: utf-8 -*-

import time
from enum import Enum
from json import dumps
from urllib import parse
from requests import post
from hashlib import md5
from typing import Any, Iterable, Optional, Dict
from logging import getLogger

__all__ = ['Request']


class Request:
    """请求执行类"""

    def __init__(self, host: str, app: str, secret: str, auth: str = None, sign_method: str = None):
        """
        构造函数
        :param host: 接口网关地址
        :param app: 应用 appkey
        :param secret: 应用密钥
        :param auth: 授权码 (可选)
        :param sign_method: 签名方式 (可选)
        """
        self._host = _strip(host)
        self._app = _strip(app)
        self._secret = _strip(secret)
        self._auth = _strip(auth)
        self._sign_method = _strip(sign_method)
        self._fetch()
        self._timeout = 60

    def timeout(self, timeout: float):
        """
        设置超时时长
        :param timeout: 超时时长 (单位: 秒)
        :return: 请求执行类实体
        """
        self._timeout = timeout
        return self

    def request(self, path: str, data: Dict[str, Any]) -> Optional[str]:
        """
        执行请求
        :param path: 接口路径
        :param data: 请求参数
        :return: 响应内容
        """
        uri = self._uri(_strip(path))
        if not uri: return
        body = self._parameters(data)
        return self._post(uri, body)

    def join_curl(self, path: str, data: Dict[str, Any], timestamp: int = None) -> str:
        """
        拼接 curl 命令串
        :param path: 接口路径
        :param data: 请求参数
        :param timestamp: 时间戳
        :return: curl 命令串
        """
        uri = self._uri(_strip(path))
        if not uri: return ''
        ts = str(timestamp) if timestamp else None
        body = self._parameters(data, ts, True)
        curl = f'curl -w "\\nHTTP status: %{{http_code}}" -X POST \'{uri}\''
        if body:
            curl += ' -H "Content-Type: application/x-www-form-urlencoded"'
            ctx = body.replace('\\', '\\\\').replace('\'', '\\\'')
            curl += f' -d \'{ctx}\''
        return curl

    def _parameters(self, data: Dict, ts: str = None, sign_trace: bool = False) -> str:
        body = {}
        if data:
            for key, value in data.items():
                if not isinstance(value, str): value = _json_str(value)
                body[key] = value
        body['_app'] = self._app
        if not ts: ts = str(int(time.time() * 1000))
        body['_t'] = ts
        if self._auth is not None and (sign_trace or self._auth.strip()): body['_s'] = self._auth
        self._sign(body, sign_trace)
        return _form_join(body)

    def _post(self, uri, body: str):
        headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8', 'Accept-Encoding': 'gzip'}
        _LOG.debug(f'Connect to {uri}')
        _LOG.debug(f'POST: {body}')
        bs = body.encode(_UTF8)
        if len(bs) > 256:
            from gzip import compress
            headers['Content-Encoding'] = 'gzip'
            bs = compress(bs)
        response = post(uri, data=bs, headers=headers, timeout=self._timeout)
        txt = response.text
        _LOG.debug(f'Response: {txt}')
        return txt

    def _sign(self, body: Dict, trace: bool = False):
        skip = '_sign_kind', '_sign'
        for s in skip:
            if s in body: del body[s]

        ps = []
        ks = sorted(body.keys())
        for key in ks:
            s = _url_quote_plus(key)
            s += '='
            value = body[key]
            if value: s += _url_quote_plus(value)
            ps.append(s)

        join = '&'.join(ps)
        if self._sign_method == 'hmac':
            _sign = _sign_hmac(self._secret, join)
            body[skip[0]] = self._sign_method
            if trace: _LOG.debug(f'签名拼接串: {join}')
        else:
            _sign = _sign_md5(self._secret, join)
            if trace: _LOG.debug(f'签名拼接串: {join}')
        body[skip[1]] = _sign
        _LOG.debug(f'Sign: {_sign}')

    def _uri(self, path: str) -> Optional[str]:
        if not self._host: return
        elif not path: return
        elif not path.startswith('/'): path = '/' + path
        return self._host + path

    def _fetch(self):
        if not self._app: raise ValueError('no app key')
        if not self._secret: raise ValueError('no secret')
        while self._host and self._host.endswith('/'): self._host = self._host[0:-1]
        if not self._host: raise ValueError('no host')
        if '/api' not in self._host: self._host += '/api'
        if self._sign_method: self._sign_method = self._sign_method.lower()


_UTF8 = 'UTF-8'
_LOG = getLogger('open.hopen')


def _strip(s: str) -> str:
    return s.strip() if s else s


def _json_str(o) -> str:
    o = conv_obj(o)
    return dumps(o, indent=None, separators=(',', ':'), ensure_ascii=False)


def _form_join(body: Dict) -> str:
    ps = []
    for key, value in body.items():
        s = _url_quote_plus(key)
        s += '='
        if value: s += _url_quote_plus(value)
        ps.append(s)
    return '&'.join(ps)


def _url_quote_plus(s: str) -> str:
    """
    url 参数转义
    :param s: 原文
    :return: 转义后文本
    """
    return parse.quote_plus(s, safe='_-.*', encoding=_UTF8)


def conv_obj(src: Any):
    """
    转换为基本类型值
    :param src: 数据实例
    :return: 基本类型值
    """
    if isinstance(src, tuple):  # 元组
        tar = map(conv_obj, src)
        return tuple(tar)
    elif isinstance(src, Enum):
        return src.name
    elif isinstance(src, dict):  # 字典
        tar = {}
        for key, value in src.items():
            k_obj = conv_obj(key)
            v_obj = conv_obj(value)
            if k_obj is None: k_obj = key
            tar[k_obj] = value if v_obj is None else v_obj
        return tar
    elif _is_iterable(src):  # 列表
        tar = map(conv_obj, src)
        return list(tar)

    stype = str(type(src))
    if '.' not in stype:  # 基本类型，无需转换
        return src
    elif 'datetime' in stype:  # 时间类型
        return str(src)
    else:  # 自定义类型
        tar = {}
        for name in [na for na in dir(src) if not na.startswith('_')]:
            attr = getattr(src, name)
            if callable(attr): continue
            elif attr is None: continue
            while name.endswith('_'): name = name[0:-1]
            tar[name] = conv_obj(attr)
        return tar


def _is_iterable(src) -> bool:
    if not isinstance(src, Iterable): return False
    elif isinstance(src, str): return False
    elif isinstance(src, bytes): return False
    return True


def _sign_hmac(secret: str, s: str) -> str:
    import hmac
    bs = hmac.new(secret.encode(_UTF8), s.encode(_UTF8), digestmod=md5)  # 计算 HmacMD5 加密值
    return bs.hexdigest().lower()  # 转十六进制值


def _sign_md5(secret: str, s: str) -> str:
    s = secret + s + secret  # 将参数串前后拼上密钥 如 ${secret}key1=value1&key2=value2${secret}
    return md5(s.encode(_UTF8)).hexdigest().lower()  # 计算 MD5 的十六进制值
