from rest_framework.throttling import UserRateThrottle

class OTPThrottle(UserRateThrottle):
    rate = '3/minute'
