"""FraudDNA Risk Simulation API Endpoints.

POST /api/v1/simulations          - Run a single simulation
POST /api/v1/simulations/compare  - Compare multiple threshold configurations
GET  /api/v1/simulations/{id}     - Retrieve cached simulation result
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.simulation.engine import SimulationEngine, get_simulation_engine
from app.simulation.schemas import (
    SimulationCompareRequest,
    SimulationCompareResponse,
    SimulationRequest,
    SimulationResult,
    generate_comparison_id,
)

router = APIRouter(prefix="/simulations", tags=["Risk Simulation"])

# In-memory result cache
_simulation_cache: dict[str, SimulationResult] = {}
_comparison_cache: dict[str, SimulationCompareResponse] = {}


@router.post(
    "",
    response_model=SimulationResult,
    summary="Run Risk Simulation",
    description="Execute a deterministic threshold simulation against the existing dataset.",
    status_code=status.HTTP_200_OK,
)
async def run_simulation(
    request: SimulationRequest,
    engine: SimulationEngine = Depends(get_simulation_engine),
) -> SimulationResult:
    """Run a single simulation with the provided configuration."""
    try:
        result = engine.run_simulation(request.config)
        _simulation_cache[result.simulation_id] = result
        return result
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation execution failed: {e}",
        ) from e


@router.post(
    "/compare",
    response_model=SimulationCompareResponse,
    summary="Compare Threshold Configurations",
    description="Run simulations for multiple configurations and return structured comparison.",
    status_code=status.HTTP_200_OK,
)
async def compare_simulations(
    request: SimulationCompareRequest,
    engine: SimulationEngine = Depends(get_simulation_engine),
) -> SimulationCompareResponse:
    """Compare multiple threshold configurations side by side."""
    try:
        results = [engine.run_simulation(cfg) for cfg in request.configs]
        for r in results:
            _simulation_cache[r.simulation_id] = r

        comparison_id = generate_comparison_id(request.configs)
        response = SimulationCompareResponse(
            comparison_id=comparison_id,
            results=results,
            baseline_index=0,
        )
        _comparison_cache[comparison_id] = response
        return response
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison execution failed: {e}",
        ) from e


@router.get(
    "/{simulation_id}",
    response_model=SimulationResult,
    summary="Get Simulation Result",
    description="Retrieve a previously computed simulation result by ID.",
)
async def get_simulation(
    simulation_id: str,
) -> SimulationResult:
    """Retrieve a cached simulation result."""
    result = _simulation_cache.get(simulation_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found.",
        )
    return result
