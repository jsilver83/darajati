# Generated by Django 2.0.1 on 2019-01-01 10:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('grade', '0019_auto_20181230_1245'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION total_rounding(
                student_total numeric,
                rounding_func text,
                decimal_places numeric)
              RETURNS numeric AS
            $BODY$
                DECLARE
                  total_after_rounding numeric;
                BEGIN
                      IF student_total IS NOT NULL THEN
                          IF rounding_func IN ('ceil', 'floor') THEN
                              execute  'SELECT ' || rounding_func || '(' || student_total || ')' into  total_after_rounding;
                          ELSIF rounding_func IN ('round', 'trunc') THEN
                              decimal_places = COALESCE(decimal_places, 0);
                              execute  'SELECT ' || rounding_func || '(' || student_total || ', ' || decimal_places || ')' into  total_after_rounding;
                          ELSE  -- rounding function is null or equal to 'none'
                              return student_total;
                          END IF;
                      ELSE
                          return 0.00;
                      END IF;
                      return total_after_rounding;
                END;
            $BODY$
            LANGUAGE plpgsql IMMUTABLE
            """
        ),
    ]
