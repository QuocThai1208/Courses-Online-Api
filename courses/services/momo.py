import json
import uuid
from urllib.parse import quote

import requests
import hmac
import hashlib

from courses.models import UserCourse, CourseStatus, Course

# parameters send to MoMo get get payUrl
endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
partnerCode = "MOMO"
accessKey = "F8BBA842ECF85"
secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
# orderInfo = "pay with MoMo"
# Sau khi thanh toán momo sẽ redirect về url này
redirectUrl = "https://webhook.site/b3088a6a-2d17-4f8d-a383-71389a6c600b"
# url thồng báo trạng thái thanh toán
ipnUrl = "http://127.0.0.1:8000/payment/momo/ipn/"

requestType = "captureWallet"


def create_momo_payment(amount, extraData, course_name):
    orderInfo = f"Thanh toán khóa học {course_name}"  # tiếng Việt gốc
    orderInfo_encoded = quote(orderInfo)
    orderId = str(uuid.uuid4())
    requestId = str(uuid.uuid4())
    amount = str(int(amount))
    extraData = str(extraData) if extraData else ""

    #tạo chuỗi đúng thứ tự
    rawSignature = (
            "accessKey=" + accessKey +
            "&amount=" + amount +
            "&extraData=" + extraData +
            "&ipnUrl=" + ipnUrl +
            "&orderId=" + orderInfo_encoded +
            "&orderInfo=" + orderInfo +
            "&partnerCode=" + partnerCode +
            "&redirectUrl=" + redirectUrl +
            "&requestId=" + requestId +
            "&requestType=" + requestType
    )

    #tạo chữ ký số
    h = hmac.new(bytes(secretKey, 'utf-8'),
                 bytes(rawSignature, 'utf-8'),
                 hashlib.sha256)
    signature = h.hexdigest()

    data = {
        'partnerCode': partnerCode,
        'partnerName': "Test",
        'storeId': "MomoTestStore",
        'requestId': requestId,
        'amount': amount,
        'orderId': orderId,
        'orderInfo': orderInfo,
        'redirectUrl': redirectUrl,
        'ipnUrl': ipnUrl,
        'lang': "vi",
        'extraData': extraData,
        'requestType': requestType,
        'signature': signature
    }
    data = json.dumps(data)
    response = requests.post(endpoint, data=data,
                             headers={'Content-Type': 'application/json',
                                      'Content-Length': str(len(data))})
    resp = response.json()
    return resp.get('payUrl')


def update_status_user_course(id, success):
    user_course = UserCourse.objects.select_for_update().get(id=id)
    if success:
        user_course.status = CourseStatus.PENDING
    else:
        user_course.status = CourseStatus.PAYMENT_FAILED
    user_course.save()
