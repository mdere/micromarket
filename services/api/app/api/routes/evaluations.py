from fastapi import APIRouter

router = APIRouter()


@router.post("/refresh")
def refresh_evaluations() -> dict[str, str]:
    return {
        "status": "accepted",
        "message": "Evaluation refresh scaffold. Outcome evaluation is next.",
    }


@router.get("/summary")
def evaluation_summary() -> dict[str, object]:
    return {
        "evaluated_forecasts": 0,
        "message": "Evaluation summary scaffold. Metrics implementation is next.",
    }
