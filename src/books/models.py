# Create your models here.
from django.db import models
from django.db.models import F


class Author(models.Model):
    full_name = models.CharField()

    def __str__(self):
        return self.full_name


class Book(models.Model):
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name="authors",
    )
    title = models.CharField()
    curr = models.CharField(max_length=3)
    price = models.FloatField()
    publish_date = models.DateField()
    query_date = models.DateTimeField()
    rate = models.FloatField()
    tableNo = models.CharField()
    pricePLN = models.GeneratedField(
        expression=F("rate") * F("price"),
        output_field=models.FloatField(),
        db_persist=True,
    )

    def __str__(self):
        return self.title + self.author.full_name

    class Meta:
        ordering = ["-query_date"]
