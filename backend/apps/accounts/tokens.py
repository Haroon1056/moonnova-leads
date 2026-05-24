from django.contrib.auth.tokens import PasswordResetTokenGenerator

class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    pass

password_reset_token = CustomPasswordResetTokenGenerator()