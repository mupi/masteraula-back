# -*- coding: utf-8 -*-
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

import datetime
from dateutil import relativedelta

#populated by fixture
class TermsUse (models.Model):
    content = models.TextField()
    last_update = models.DateTimeField(auto_now=True)


