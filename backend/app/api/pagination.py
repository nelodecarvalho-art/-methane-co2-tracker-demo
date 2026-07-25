from sqlalchemy.orm import Query


def paginate(query: Query, limit: int, offset: int) -> tuple[list, int]:
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return items, total
