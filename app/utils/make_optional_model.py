from typing import Type, Optional

from pydantic import BaseModel, Field, create_model


def make_optional_model(model: Type[BaseModel], name_suffix="Update") -> Type[BaseModel]:
    """Creates a new model where all fields are optional with the same aliases."""
    fields = {}

    for field_name, field_type in model.__annotations__.items():
        # Get the original field to preserve aliases and other metadata
        original_field = model.model_fields.get(field_name)

        if original_field and original_field.alias:
            # Create a new optional field with the same alias
            fields[field_name] = (Optional[field_type], Field(default=None, alias=original_field.alias))
        else:
            # If no alias, just make it optional
            fields[field_name] = (Optional[field_type], None)

    return create_model(
        f"{model.__name__}{name_suffix}",
        **fields,
        __base__=model
    )
