from sqlalchemy.orm import Session
from sqlalchemy import text

class CarouselRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_images(self):
        """Get all carousel images ordered by display_order."""
        query = text("""
            SELECT image_url 
            FROM saga.carousel_images 
            ORDER BY display_order ASC
        """)
        result = self.db.execute(query)
        return [row[0] for row in result.fetchall()]
    
    def update_images(self, image_urls: list):
        """Replace all carousel images with new list."""
        # Delete existing images
        delete_query = text("DELETE FROM saga.carousel_images")
        self.db.execute(delete_query)
        
        # Insert new images with order
        for index, url in enumerate(image_urls):
            insert_query = text("""
                INSERT INTO saga.carousel_images (image_url, display_order)
                VALUES (:url, :order)
            """)
            self.db.execute(insert_query, {"url": url, "order": index})
        
        self.db.commit()