from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class FriendRequest(models.Model):

    from_user = models.ForeignKey(User, related_name='sent_friend_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_friend_requests', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(default='pending')

   
    class Meta:
        unique_together = ('from_user', 'to_user')



class Friend(models.Model):
    user = models.ForeignKey(User, related_name='friends', on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='friend_of', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} is friends with {self.friend}"

    class Meta:
        unique_together = ('user', 'friend')