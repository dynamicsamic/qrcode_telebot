from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from settings import settings


class Base(DeclarativeBase):
    pass


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    value: Mapped[str] = mapped_column(unique=True, index=True)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(Id={self.id}), Val={self.value}"


engine = create_async_engine(
    "postgresql+asyncpg://test_user:test_user@localhost:5432/test_qrcode",
    echo=settings.DEBUG,
)


class Repo:
    def __init__(self) -> None:
        self.sessionmaker = async_sessionmaker(
            bind=engine, expire_on_commit=False, autoflush=False
        )

    async def add(self, value: str) -> int:
        async with self.sessionmaker() as session, session.begin():
            entry_id = await session.execute(
                insert(Entry).values(value=value).returning(Entry.id)
            )
            await session.commit()
        return entry_id

    async def delete(self, entry_id: int) -> int:
        async with self.sessionmaker() as session, session.begin():
            deleted = await session.execute(delete(Entry).where(Entry.id == entry_id))
            await session.commit()
        return deleted.rowcount

    async def get_entry_id(self, value: str) -> int:
        async with self.sessionmaker() as session, session.begin():
            return (
                await session.scalars(select(Entry.id).where(Entry.value == value))
            ).first()
