import os
import shutil
from PIL import Image
import glob

class ImageManager:
    def __init__(self, base_dir="./viewer/captures"):
        self.base_dir = base_dir
        self.current_index = 0
        self.images = []
        
        # Create captures directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        
        # Load existing images on startup
        self.load_existing_images()
        
    def load_existing_images(self):
        """Load all existing PNG images from the captures directory"""
        self.images = []
        # Get all PNG files and sort them by name
        png_files = glob.glob(os.path.join(self.base_dir, "capture_*.png"))
        png_files.sort()  # Sort to maintain sequence
        
        # Add existing files to our list
        for filepath in png_files:
            if os.path.exists(filepath):  # Double check file exists
                self.images.append(filepath)
                
        print(f"Loaded {len(self.images)} existing captures")
        
    def refresh_images(self):
        """Refresh the image list by scanning directory"""
        current_file = self.images[self.current_index] if self.images else None
        self.load_existing_images()
        
        # Try to maintain the current index
        if current_file and current_file in self.images:
            self.current_index = self.images.index(current_file)
        else:
            self.current_index = 0
        
    def add_image(self, image):
        # Save image with sequential name
        next_number = 0
        if self.images:
            # Get the last file number and increment
            last_file = os.path.basename(self.images[-1])
            try:
                next_number = int(last_file.split('_')[1].split('.')[0]) + 1
            except:
                pass
                
        filename = f"capture_{next_number:03d}.png"
        filepath = os.path.join(self.base_dir, filename)
        image.save(filepath)
        self.images.append(filepath)
        
    def clear_images(self):
        # Remove all captured images
        for img in self.images:
            if os.path.exists(img):
                try:
                    os.remove(img)
                except Exception as e:
                    print(f"Error removing {img}: {e}")
        self.images = []
        self.current_index = 0
        
    def show_current(self):
        if not self.images:
            return False
            
        # Refresh image list before showing
        self.refresh_images()
        
        if not self.images:  # Check again after refresh
            return False
            
        # Make sure current_index is valid
        self.current_index = min(self.current_index, len(self.images) - 1)
        
        # Copy current image to res.png
        try:
            shutil.copy2(self.images[self.current_index], "./viewer/res.png")
            return True
        except Exception as e:
            print(f"Error showing image: {e}")
            return False
        
    def next_image(self):
        if not self.images:
            return False
        self.refresh_images()  # Refresh before changing image
        if self.images:  # Check again after refresh
            self.current_index = (self.current_index + 1) % len(self.images)
            return self.show_current()
        return False
        
    def prev_image(self):
        if not self.images:
            return False
        self.refresh_images()  # Refresh before changing image
        if self.images:  # Check again after refresh
            self.current_index = (self.current_index - 1) % len(self.images)
            return self.show_current()
        return False
        
    def show_last(self):
        """Show the most recently captured image"""
        if not self.images:
            return False
        self.current_index = len(self.images) - 1
        return self.show_current()
        
    def show_first(self):
        """Show the first captured image"""
        print("try show_first")
        if not self.images:
            return False
        print("show_first")
        self.current_index = 0
        return self.show_current() 