import json
import uuid

import requests
import hmac
import hashlib

from courses.models import UserCourse, CourseStatus, Course, Payment

# parameters send to MoMo get get payUrl
endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
partnerCode = "MOMO"
accessKey = "F8BBA842ECF85"
secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
orderInfo = "pay with MoMo"
# Sau khi thanh toán momo sẽ redirect về url này
redirectUrl = "https://webhook.site/b3088a6a-2d17-4f8d-a383-71389a6c600b"
# url thồng báo trạng thái thanh toán
# ipnUrl = "https://9cf58300a6e7.ngrok-free.app/payment/momo/ipn/"
ipnUrl = "http://160.25.81.159:8080/payment/momo/ipn/"

requestType = "captureWallet"


def create_momo_payment(user, amount, extraData):
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
            "&orderId=" + orderId +
            "&orderInfo=" + orderInfo +
            "&partnerCode=" + partnerCode +
            "&redirectUrl=" + redirectUrl +
            "&requestId=" + requestId +
            "&requestType=" + requestType
    )

    #tạo chữ ký số
    h = hmac.new(bytes(secretKey, 'ascii'),
                 bytes(rawSignature, 'ascii'),
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
    pay_url = resp.get('payUrl')
    payment = Payment.objects.create(
        id=orderId,
        user=user,
        course=extraData,
        amount=amount,
    )
    if pay_url:
        payment.save()
    return pay_url


def update_status_user_course(id, status):
    user_course = UserCourse.objects.get(id=id)
    user_course.status = status
    user_course.save()
