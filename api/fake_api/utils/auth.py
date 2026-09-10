from fake_api.response import Response


def check_api_key(config):
    if config.client_api_key != config.expected_api_key:
        return Response(
            status_code=401,
            error="Unauthorized",
        )

    return None
