from rest_framework.throttling import UserRateThrottle


class RegisterThrottle(UserRateThrottle):
    scope = 'register'

class LoginThrottle(UserRateThrottle):
    scope = 'login'
