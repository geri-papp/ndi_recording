from fastapi.routing import APIRoute


def custom_generate_unique_id(route: APIRoute):
    if len(route.tags) == 0:
        return route.name
    return f"{route.tags[0]}-{route.name}"
