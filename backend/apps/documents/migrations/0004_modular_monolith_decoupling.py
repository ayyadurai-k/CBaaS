# Generated migration for modular monolith decoupling
# Phase 1: Replace FK with UUID reference field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0003_alter_embedding_dimensions'),
    ]

    operations = [
        # Step 1: Remove the FK to Organization
        migrations.RemoveField(
            model_name='document',
            name='organization',
        ),
        
        # Step 2: Add the new UUID reference field
        migrations.AddField(
            model_name='document',
            name='organization_id',
            field=models.UUIDField(
                db_index=True,
                help_text='Reference to Organization in Identity Service',
                # Temporarily allow null for migration
                null=True,
            ),
            preserve_default=False,
        ),
        
        # Step 3: Update indexes to use organization_id
        migrations.RemoveIndex(
            model_name='document',
            name='documents_d_organiz_428f7c_idx',
        ),
        migrations.RemoveIndex(
            model_name='document',
            name='documents_d_organiz_name_idx',
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(
                fields=['organization_id', 'upload_date'],
                name='documents_d_org_id_upload_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(
                fields=['organization_id', 'name'],
                name='documents_d_org_id_name_idx'
            ),
        ),
    ]
