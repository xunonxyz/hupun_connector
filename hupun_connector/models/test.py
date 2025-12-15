
from . import hupun_request

def call_api():
    base_url = "https://open-api.hupun.com/api"
    path = "/erp/base/shop/page/get"
    url = f"{base_url}{path}"

    # 假设data是一个包含所有参数的字典
    data = {
        # 向data中添加业务参数并完成签名，将得到系统参数一并添加到data中
    }

    try:
        response = hupun_request.post(url, data=data)
        print(response.text)
    except Exception as e:
        print("Error calling the API:", e)

call_api()