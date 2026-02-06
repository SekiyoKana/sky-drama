import os
import logging
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.db.session import SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)

def clean_orphan_assets():
    """
    Clean up asset files that are not recorded in the database.
    Excludes 'static' and 'styles' directories.
    """
    assets_dir = settings.ASSETS_DIR
    if not os.path.exists(assets_dir):
        logger.warning(f"Assets directory '{assets_dir}' does not exist. Skipping cleanup.")
        return

    db: Session = SessionLocal()
    try:
        valid_urls = db.query(Asset.url).all()
        
        valid_files = set()
        for (url,) in valid_urls:
            if url and url.startswith("/assets/"):
                filename = url.replace("/assets/", "", 1)
                valid_files.add(filename)
            elif url and url.startswith("assets/"):
                 filename = url.replace("assets/", "", 1)
                 valid_files.add(filename)

    except Exception as e:
        logger.error(f"Failed to query assets from DB: {e}")
        return
    finally:
        db.close()

    cleaned_count = 0
    
    try:
        for filename in os.listdir(assets_dir):
            file_path = os.path.join(assets_dir, filename)
            
            if os.path.isdir(file_path):
                continue
                
            if filename.startswith("."): 
                continue

            if filename not in valid_files:
                try:
                    os.remove(file_path)
                    logger.info(f"🗑️ Deleted orphan asset: {filename}")
                    cleaned_count += 1
                except OSError as e:
                    logger.error(f"Error deleting file {file_path}: {e}")

        if cleaned_count > 0:
            logger.info(f"✅ Cleaned {cleaned_count} orphan assets.")
        else:
            logger.info("✨ No orphan assets found.")

    except Exception as e:
        logger.error(f"Error during asset cleanup: {e}")
