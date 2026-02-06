# Generated migration for modular monolith decoupling
# Phase 1: Replace FK with UUID reference field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0003_increase_api_key_length'),
    ]

    operations = [
        # Step 1: Remove the M2M field (documents_connected)
        migrations.RemoveField(
            model_name='chatbot',
            name='documents_connected',
        ),
        
        # Step 2: Remove the FK to Organization
        migrations.RemoveField(
            model_name='chatbot',
            name='organization',
        ),
        
        # Step 3: Add the new UUID reference field
        migrations.AddField(
            model_name='chatbot',
            name='organization_id',
            field=models.UUIDField(
                db_index=True,
                help_text='Reference to Organization in Identity Service',
                # Temporarily allow null for migration, will be updated
                null=True,
            ),
            preserve_default=False,
        ),
        
        # Step 4: Add JSONField for document IDs
        migrations.AddField(
            model_name='chatbot',
            name='connected_document_ids',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='List of Document UUIDs from Knowledge Service'
            ),
        ),
        
        # Step 5: Remove old unique_together constraint
        migrations.AlterUniqueTogether(
            name='chatbot',
            unique_together=set(),
        ),
        
        # Step 6: Add new unique constraint
        migrations.AddConstraint(
            model_name='chatbot',
            constraint=models.UniqueConstraint(
                fields=['organization_id'],
                name='unique_chatbot_per_organization'
            ),
        ),
        
        # Step 7: Update index to use organization_id
        migrations.RemoveIndex(
            model_name='chatbot',
            name='chatbot_cha_organiz_e04dbc_idx',
        ),
        migrations.AddIndex(
            model_name='chatbot',
            index=models.Index(
                fields=['organization_id', 'created_at'],
                name='chatbot_cha_organiz_new_idx'
            ),
        ),
    ]
