Kitworks Base Mixins Module
===========================
.. |badge1| image:: https://img.shields.io/badge/license-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |badge2| image:: https://img.shields.io/badge/maintainer-Kitworks-purple.png
    :target: https://kitworks.systems/
    
.. |badge3| image:: https://img.shields.io/badge/docs-Base_Mixins-yellowgreen.png
    :target: https://kitworks.systems/

|badge1| |badge2| |badge3|

Kitworks Base Mixins is a technical module developed by `Kitworks Systems <https://kitworks.systems/>`__. 

This module provides a collection of reusable mixins for Odoo models. These mixins enhance model functionality with various date-related operations, string processing, and utility methods.

Key Features
------------

- **Date Parts Processing**
    - Year-based operations and computations
    - Week number handling and calculations
    - Month-based operations and validations
    - Quarter operations and validations
    - Day of week utilities and name conversions

- **Date Extraction**
    - Extract dates from strings
    - Convert integers to dates
    - Handle various datetime formats
    - Timezone-aware conversions

- **String Processing**
    - Text transliteration utilities
    - String cleaning and normalization
    - KMU rules-based transliteration
    - Special character handling

Usage Examples
--------------

1. Using Year Mixin:
   
   .. code-block:: python

       class MyModel(models.Model):
           _name = 'my.model'
           _inherit = ['year.mixin']

           # Now you have access to year-related fields and methods
           def my_method(self):
               current_year = self.year_get_current()
               fiscal_year = self.year_get_fiscal()

2. Using Week Mixin:

   .. code-block:: python

       class MyModel(models.Model):
           _name = 'my.model'
           _inherit = ['week.mixin']

           def my_method(self):
               week_number = self.week_get_number()
               week_dates = self.week_get_dates()

3. Using String Processing:

   .. code-block:: python

       class MyModel(models.Model):
           _name = 'my.model'
           _inherit = ['transliterate.mixin']

           def my_method(self):
               clean_text = self.string_clean('Some text')
               trans_text = self.string_transliterate('Текст')


Bug Tracker
-----------

Bugs are tracked on `Kitworks Support <https://kitworks.systems/requests>`_.
In case of trouble, please check there if your issue has already been reported.

Maintainer
----------

.. image:: https://kitworks.systems/logo.png
   :alt: Kitworks Systems
   :target: https://kitworks.systems

This module is maintained by Kitworks Systems.

We can provide you further Odoo Support, Odoo implementation, Odoo customization, Odoo 3rd Party development and integration software, consulting services. Our main goal is to provide the best quality product for you.

For any questions `contact us <mailto:support@kitworks.systems>`__.
