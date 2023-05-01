from django.conf import settings
from django.db import models

from forum.models import Question
from wiwik_lib.models import AdvancedModelManager, user_model_defer_fields


class QuestionInviteToAnswer(models.Model):
    """
    Invite a user to answer a question.
    This data will be added to the question data.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, blank=False, related_name='invitations')
    invitee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    objects = AdvancedModelManager(
        select_related=('invitee',), deferred_fields=user_model_defer_fields('invitee'))

    class Meta:
        verbose_name_plural = 'Question Invitations'


class QuestionBookmark(models.Model):
    """
    Represents a bookmark of a user.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, blank=False, related_name='bookmarks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)
    objects = AdvancedModelManager(
        select_related=('question',), )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super(QuestionBookmark, self).save(force_insert, force_update, using, update_fields)
        self.user.bookmarks_count = QuestionBookmark.objects.filter(user=self.user).count()
        self.user.save()

    def delete(self, using=None, keep_parents=False):
        super(QuestionBookmark, self).delete(using, keep_parents)
        self.user.bookmarks_count = QuestionBookmark.objects.filter(user=self.user).count()
        self.user.save()
