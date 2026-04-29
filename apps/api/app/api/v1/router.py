from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.modules.ai_evaluation.router import router as ai_evaluation_router
from app.modules.attempts.router import router as attempts_router
from app.modules.auth.router import router as auth_router
from app.modules.content.router import router as content_router
from app.modules.evaluation.router import router as evaluation_router
from app.modules.lab_progress.router import router as lab_progress_router
from app.modules.labs.router import router as labs_router
from app.modules.leaderboard.router import router as leaderboard_router
from app.modules.paths.router import router as paths_router
from app.modules.paths.modules_router import router as modules_router
from app.modules.progress.router import router as progress_router
from app.modules.scoring.router import router as scoring_router
from app.modules.users.router import router as users_router


v1_router = APIRouter()
v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(paths_router)
v1_router.include_router(modules_router)
v1_router.include_router(labs_router)
v1_router.include_router(lab_progress_router)
v1_router.include_router(content_router)
v1_router.include_router(attempts_router)
v1_router.include_router(evaluation_router)
v1_router.include_router(scoring_router)
v1_router.include_router(progress_router)
v1_router.include_router(leaderboard_router)
v1_router.include_router(ai_evaluation_router)
v1_router.include_router(health_router)
