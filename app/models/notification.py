from app.db.crud import MongoCrud
from app.schema import notification as notification_schema


class NotificationModel(MongoCrud[notification_schema.NotificationDocument]):
    def __init__(self):
        super().__init__(notification_schema.NotificationDocument)
