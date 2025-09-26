# Generated migration to change embedding dimensions from 1536 to 768 for Gemini
from django.db import migrations
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0002_rename_doc_org_uploaddate_idx_documents_d_organiz_428f7c_idx_and_more"),
    ]

    operations = [
        # First, drop the existing vector index
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS docchunk_embedding_ivfflat;",
            reverse_sql="CREATE INDEX IF NOT EXISTS docchunk_embedding_ivfflat "
                        "ON documents_documentchunk USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);",
        ),
        
        # Clear existing document chunks with old embeddings
        # This is necessary because we can't convert 1536D vectors to 768D automatically
        migrations.RunSQL(
            sql="DELETE FROM documents_documentchunk;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        
        # Reset document status to processing so they get re-processed with new embeddings
        migrations.RunSQL(
            sql="UPDATE documents_document SET status = 'processing';",
            reverse_sql=migrations.RunSQL.noop,
        ),
        
        # Alter the embedding field to use 768 dimensions for Gemini
        migrations.AlterField(
            model_name="documentchunk",
            name="embedding",
            field=pgvector.django.VectorField(dimensions=768),
        ),
        
        # Recreate the vector index with the new dimensions
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS docchunk_embedding_ivfflat "
                "ON documents_documentchunk USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);",
            reverse_sql="DROP INDEX IF EXISTS docchunk_embedding_ivfflat;",
        ),
    ]