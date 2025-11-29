from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from typing import Literal
from sqlalchemy.orm import Session
from sqlalchemy import distinct, union

from velocitrack.database import get_db, engine
from velocitrack.models import (
    Base,
    VelocityModel1D,
    VelocityModel3D_VP,
    VelocityModel3D_VS,
    AuthorBibref,
)
from velocitrack.config import API_TITLE, API_DESCRIPTION
import velocitrack

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=velocitrack.__version__,
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def get_bibref_for_author(db: Session, author: str) -> str:
    """Get bibliographic reference for an author from the database"""
    result = db.query(AuthorBibref).filter(AuthorBibref.author.ilike(f"%{author}%")).first()
    return result.bibref if result else ""


def create_text_response_1d(models: list, bibref: str = "", total_count: int = 0, offset: int = 0, limit: int = 0) -> str:
    """Create VELEST format response for 1D velocity models"""
    if not models:
        return ""

    # Separate VP and VS models
    vp_models = [m for m in models if m.wave_type == "VP"]
    vs_models = [m for m in models if m.wave_type == "VS"]

    # Sort by depth
    vp_models.sort(key=lambda x: x.depth)
    vs_models.sort(key=lambda x: x.depth)

    lines = []

    # Header - use NFO and bibref to create title
    nfo = models[0].nfo if models else "Unknown"
    if bibref:
        lines.append(f"1D {nfo} {bibref}")
    else:
        lines.append(f"1D {nfo}")

    # Add pagination info if there's more data
    if total_count > len(models):
        lines.append(f"# Showing {offset + 1}-{offset + len(models)} of {total_count} records (limit={limit}, offset={offset})")

    # VP section
    if vp_models:
        lines.append(
            f" {len(vp_models)}        vel,depth,vdamp,phase (f5.2,5x,f7.2,2x,f7.3,3x,a1)"
        )
        for i, model in enumerate(vp_models):
            vel_str = f"{model.velocity:4.2f}"

            # Match exact VELEST format spacing
            if model.depth < 0:
                # Negative numbers: 7 spaces, format as -X.XX
                depth_str = f"{model.depth:5.2f}"
                spacing = "       "  # 7 spaces
            elif model.depth >= 10:
                # Double digit positive: 7 spaces, format as XX.XX
                depth_str = f"{model.depth:5.2f}"
                spacing = "       "  # 7 spaces
            else:
                # Single digit positive: 8 spaces, format as X.XX
                depth_str = f"{model.depth:4.2f}"
                spacing = "        "  # 8 spaces

            if i == 0:
                lines.append(
                    f" {vel_str}{spacing}{depth_str}   001.000           P-VELOCITY MODEL"
                )
            else:
                lines.append(
                    f" {vel_str}{spacing}{depth_str}   001.000"
                )  # Separator for VS section
    if vs_models:
        lines.append(f" {len(vs_models)}")
        for i, model in enumerate(vs_models):
            vel_str = f"{model.velocity:4.2f}"

            # Match exact VELEST format spacing
            if model.depth < 0:
                # Negative numbers: 7 spaces, format as -X.XX
                depth_str = f"{model.depth:5.2f}"
                spacing = "       "  # 7 spaces
            elif model.depth >= 10:
                # Double digit positive: 7 spaces, format as XX.XX
                depth_str = f"{model.depth:5.2f}"
                spacing = "       "  # 7 spaces
            else:
                # Single digit positive: 8 spaces, format as X.XX
                depth_str = f"{model.depth:4.2f}"
                spacing = "        "  # 8 spaces

            if i == 0:
                lines.append(
                    f" {vel_str}{spacing}{depth_str}   001.000           S-VELOCITY MODEL"
                )
            else:
                lines.append(f" {vel_str}{spacing}{depth_str}   001.000")

    return "\n".join(lines)


@app.get("/3d/")
async def query_3d_velocity_models(
    wave_type: Literal["VP", "VS"] = Query(..., description="Wave type (VP or VS)"),
    author: str = Query(..., description="Author/reference to filter by"),
    include_r: bool = Query(
        False, description="Include R column in output (default: false)"
    ),
    limit: int = Query(10000, ge=1, le=100000, description="Maximum number of records to return (default: 10000, max: 100000)"),
    offset: int = Query(0, ge=0, description="Number of records to skip (default: 0)"),
):
    """
    Query 3D velocity models by wave type and author

    Returns 3D velocity model data for the specified wave type and author in tab-delimited text format.
    Use limit and offset for pagination when dealing with large datasets.
    """
    try:
        # Get database session
        db = next(get_db())
        try:
            # Select the appropriate model class
            if wave_type == "VP":
                model_class = VelocityModel3D_VP
            else:
                model_class = VelocityModel3D_VS

            # Get total count first
            total_count = (
                db.query(model_class)
                .filter(model_class.author.ilike(f"%{author}%"))
                .count()
            )

            # Check if no data exists at all
            if total_count == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"No {wave_type} data found for author: {author}",
                )

            # Check if offset exceeds available data
            if offset >= total_count:
                raise HTTPException(
                    status_code=400,
                    detail=f"Offset {offset} exceeds total records ({total_count}). Max offset: {total_count - 1}",
                )

            # Build query - filter by author and order by longitude, latitude, depth
            query = (
                db.query(model_class)
                .filter(model_class.author.ilike(f"%{author}%"))
                .order_by(
                    model_class.longitude.asc(),
                    model_class.latitude.asc(),
                    model_class.depth.asc(),
                )
                .offset(offset)
                .limit(limit)
            )

            # Execute query
            models = query.all()

            # Get bibref for the author
            bibref = get_bibref_for_author(db, author)

            # Return tab-delimited text format with pagination info
            content = create_text_response_3d(models, wave_type, include_r, bibref, total_count, offset, limit)
            return PlainTextResponse(content=content)

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/")
def root():
    return {"service": API_TITLE, "version": velocitrack.__version__}


@app.get("/authors")
async def get_authors(db: Session = Depends(get_db)):
    """Return all unique authors from all velocity model tables"""
    try:
        # Collect authors from all tables
        authors_set = set()

        # Get authors from 1D table
        authors_1d = (
            db.query(distinct(VelocityModel1D.author))
            .filter(VelocityModel1D.author.isnot(None))
            .all()
        )
        for author in authors_1d:
            if author[0]:
                authors_set.add(author[0])

        # Get authors from 3D VP table
        authors_3d_vp = (
            db.query(distinct(VelocityModel3D_VP.author))
            .filter(VelocityModel3D_VP.author.isnot(None))
            .all()
        )
        for author in authors_3d_vp:
            if author[0]:
                authors_set.add(author[0])

        # Get authors from 3D VS table
        authors_3d_vs = (
            db.query(distinct(VelocityModel3D_VS.author))
            .filter(VelocityModel3D_VS.author.isnot(None))
            .all()
        )
        for author in authors_3d_vs:
            if author[0]:
                authors_set.add(author[0])

        # Format as newline-separated text
        author_names = sorted(list(authors_set))
        return PlainTextResponse("\n".join(author_names) + "\n")
    except Exception as e:
        # Fallback to empty response if database query fails
        return PlainTextResponse("")


@app.get("/nfos")
async def get_nfos(db: Session = Depends(get_db)):
    """Return all unique NFOs from all velocity model tables"""
    try:
        # Collect NFOs from all tables
        nfos_set = set()

        # Get NFOs from 1D table
        nfos_1d = (
            db.query(distinct(VelocityModel1D.nfo))
            .filter(VelocityModel1D.nfo.isnot(None))
            .all()
        )
        for nfo in nfos_1d:
            if nfo[0]:
                nfos_set.add(nfo[0])

        # Get NFOs from 3D VP table
        nfos_3d_vp = (
            db.query(distinct(VelocityModel3D_VP.nfo))
            .filter(VelocityModel3D_VP.nfo.isnot(None))
            .all()
        )
        for nfo in nfos_3d_vp:
            if nfo[0]:
                nfos_set.add(nfo[0])

        # Get NFOs from 3D VS table
        nfos_3d_vs = (
            db.query(distinct(VelocityModel3D_VS.nfo))
            .filter(VelocityModel3D_VS.nfo.isnot(None))
            .all()
        )
        for nfo in nfos_3d_vs:
            if nfo[0]:
                nfos_set.add(nfo[0])

        # Format as newline-separated text
        nfo_names = sorted(list(nfos_set))
        return PlainTextResponse("\n".join(nfo_names) + "\n")
    except Exception as e:
        # Fallback to empty response if database query fails
        return PlainTextResponse("")


@app.get("/1d/")
async def query_1d_velocity_models(
    author: str = Query(..., description="Author/reference to filter by"),
    nfo: str = Query(..., description="Network/Organization identifier to filter by"),
    limit: int = Query(10000, ge=1, le=100000, description="Maximum number of records to return (default: 10000, max: 100000)"),
    offset: int = Query(0, ge=0, description="Number of records to skip (default: 0)"),
):
    """
    Query 1D velocity models by author and NFO

    Returns velocity model data for the specified author and NFO in VELEST format.
    Use limit and offset for pagination when dealing with large datasets.
    """
    try:
        # Get database session
        db = next(get_db())
        try:
            # Get total count first
            total_count = (
                db.query(VelocityModel1D)
                .filter(
                    VelocityModel1D.author.ilike(f"%{author}%"),
                    VelocityModel1D.nfo.ilike(f"%{nfo}%"),
                )
                .count()
            )

            # Check if no data exists at all
            if total_count == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for author: {author} and NFO: {nfo}",
                )

            # Check if offset exceeds available data
            if offset >= total_count:
                raise HTTPException(
                    status_code=400,
                    detail=f"Offset {offset} exceeds total records ({total_count}). Max offset: {total_count - 1}",
                )

            # Build query - filter by author and NFO, order by depth
            query = (
                db.query(VelocityModel1D)
                .filter(
                    VelocityModel1D.author.ilike(f"%{author}%"),
                    VelocityModel1D.nfo.ilike(f"%{nfo}%"),
                )
                .order_by(VelocityModel1D.depth.asc())
                .offset(offset)
                .limit(limit)
            )

            # Execute query
            models = query.all()

            # Get bibref for the author
            bibref = get_bibref_for_author(db, author)

            # Return text format with pagination info
            content = create_text_response_1d(models, bibref, total_count, offset, limit)
            return PlainTextResponse(content=content)

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def create_text_response_3d(
    models: list, wave_type: str, include_r: bool = True, bibref: str = "",
    total_count: int = 0, offset: int = 0, limit: int = 0
) -> str:
    """Create tab-delimited text format response for 3D velocity models"""
    if not models:
        return ""

    # Only show R column if user requested it AND there are non-default R values
    has_non_default_r = any(model.r != 1.0 for model in models)
    show_r = include_r and has_non_default_r

    lines = []

    # Header - use NFO and bibref to create title
    nfo = models[0].nfo if models else "Unknown"
    if bibref:
        lines.append(f"3D {nfo} {bibref}")
    else:
        lines.append(f"3D {nfo}")

    # Add pagination info if there's more data
    if total_count > len(models):
        lines.append(f"# Showing {offset + 1}-{offset + len(models)} of {total_count} records (limit={limit}, offset={offset})")

    # Create column header
    if show_r:
        header = "Longitude|Latitude|Depth|{}|R".format(
            "Vp" if wave_type == "VP" else "Vs"
        )
    else:
        header = "Longitude|Latitude|Depth|{}".format(
            "Vp" if wave_type == "VP" else "Vs"
        )

    lines.append(header)

    for model in models:
        if wave_type == "VP":
            velocity = model.vp
        else:
            velocity = model.vs

        if show_r:
            r_value = model.r if model.r is not None else 1.0
            lines.append(
                f"{model.longitude}|{model.latitude}|{model.depth}|{velocity}|{r_value}"
            )
        else:
            lines.append(
                f"{model.longitude}|{model.latitude}|{model.depth}|{velocity}"
            )

    return "\n".join(lines)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
