from copy import deepcopy
from typing import Type, Optional, Dict, Any

from pydantic import BaseModel, Field, create_model, ConfigDict


def make_optional_model(
    model: Type[BaseModel],
    *,
    name_suffix: str = "Update",
) -> Type[BaseModel]:
    """
    Build a *new* Pydantic model where every field of *model*
    becomes Optional with default None.
    """

    # 1️⃣  Copy every FieldInfo but mark it optional/None
    new_fields: Dict[str, tuple[Any, Any]] = {}
    for name, fld in model.model_fields.items():
        anno = Optional[fld.annotation]            # type: ignore[index]
        copied_info = deepcopy(fld)                # fld *is* FieldInfo
        copied_info.default = None
        new_fields[name] = (anno, copied_info)

    # 2️⃣  Merge (or create) ConfigDict and be sure populate_by_name is True
    base_cfg = getattr(model, "model_config", None)
    merged_cfg: Dict[str, Any] = dict(base_cfg or {})
    merged_cfg.setdefault("populate_by_name", True)   # only add if absent
    new_cfg = ConfigDict(**merged_cfg)                # safe now

    # 3️⃣  Create the actual model (no inheritance → no “required” bleed-through)
    return create_model(
        f"{model.__name__}{name_suffix}",
        __config__=new_cfg,
        **new_fields,
    )