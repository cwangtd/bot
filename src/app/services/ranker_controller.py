from app.models.dto import CategoryMatch
from app.models.shooter_dto import ShooterStatus, ShooterDto


class MatchRanker:
    # MatchRanker will be a family of ranker classes down the path. 000 is the default version for now.
    @staticmethod
    def ranks_000(kms: list[CategoryMatch], top_n: int = 5) -> list[dict]:
        tops = sorted(
            ((item, km) for km in kms for item in km.items[:top_n]),
            key=lambda x: x[0].score, reverse=True
        )
        ranked = [
            x[0].to_v000_response(x[1]) for x in tops
        ]
        return ranked

    @staticmethod
    def compose_standard_result(
            req_id: str,
            session_id: str,
            ranks: list[dict] = None,
            status: ShooterStatus = ShooterStatus.PENDING
    ) -> ShooterDto:
        return ShooterDto(
            request_id=req_id,
            response_id=session_id,
            ranks=ranks,
            status=status
        )
