from django.db import models

class LISStudent(models.Model):
    lrn = models.CharField(max_length=12, primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    last_school = models.CharField(max_length=255)

    class Meta:
        managed = False  # 🔥 VERY IMPORTANT
        db_table = 'lis_students'

    def __str__(self):
        return f"{self.lrn} - {self.last_name}"
