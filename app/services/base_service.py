from app.repositories.unit_of_work import UnitOfWork


class BaseService:
    unit_of_work: UnitOfWork

    def __init__(self, uow: UnitOfWork | None = None) -> None:
        self.unit_of_work = uow or UnitOfWork()
