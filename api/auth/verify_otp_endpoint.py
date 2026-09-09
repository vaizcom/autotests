def verify_otp_endpoint(temp_token, otp):
    return {
        "path": "/VerifyOtp",
        "json": {"tempToken": temp_token, "otp": otp},
        "headers": {"Content-Type": "application/json"}
    }
