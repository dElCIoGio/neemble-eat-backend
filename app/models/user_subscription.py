from app.db.crud import MongoCrud
from app.schema import user_subscription as subscription_schema

class UserSubscriptionModel(MongoCrud[subscription_schema.UserSubscriptionDocument]):
    def __init__(self) -> None:
        super().__init__(subscription_schema.UserSubscriptionDocument)
