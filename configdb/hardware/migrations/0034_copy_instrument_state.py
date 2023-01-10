from django.db import migrations

CODE_STATE_MAPPING = {0: 'DISABLED',
                      10: 'MANUAL',
                      20: 'COMMISSIONING',
                      25: 'STANDBY',
                      30: 'SCHEDULABLE'}


class Migration(migrations.Migration):
    dependencies = [
        ('hardware', '0033_alter_instrument_state'),
    ]

    def translate_state_int_to_char(apps, schema_editor):
        """Forward migration for translating from integer instrument state to character"""
        Instrument = apps.get_model('hardware', 'Instrument')
        for ins in Instrument.objects.all():
            ins.state = CODE_STATE_MAPPING[ins.state_int]
            ins.save()

    def translate_state_char_to_int(apps, schema_editor):
        """Reverse migration for translating from character instrument state back to integer"""
        Instrument = apps.get_model('hardware', 'Instrument')
        for ins in Instrument.objects.all():
            try:
                ins.state_int = next((key for key in CODE_STATE_MAPPING if CODE_STATE_MAPPING[key] == str(ins.state)), None)
                ins.save()
            except:
                print(f"Reverse migration for instrument {ins.code} failed.")
    
    operations = [
        migrations.RunPython(translate_state_int_to_char, reverse_code=translate_state_char_to_int),
        migrations.RemoveField(
            model_name='instrument',
            name='state_int'
        )
    ]
