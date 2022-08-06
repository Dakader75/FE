from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QPixmap

from app.resources.icons import Icon

class IconView(QGraphicsView):
    min_scale = 0.5
    max_scale = 5
    static_size = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setMouseTracking(True)

        self.image = None
        self.screen_scale = 1

    def set_image(self, pixmap):
        if pixmap:
            self.image = pixmap
            if not self.static_size:
                self.setSceneRect(0, 0, self.image.width(), self.image.height())
        else:
            self.image = None
            self.clear_scene()

    def clear_scene(self):
        self.scene.clear()

    def show_image(self):
        if self.image:
            self.clear_scene()
            self.scene.addPixmap(self.image)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0 and self.screen_scale < self.max_scale:
            self.screen_scale += 1
            self.scale(2, 2)
        elif event.angleDelta().y() < 0 and self.screen_scale > self.min_scale:
            self.screen_scale -= 1
            self.scale(0.5, 0.5)

def icon_slice(resource, base_width: int, base_height: int) -> list:
    if not resource.pixmap:
        resource.pixmap = QPixmap(resource.full_path)
    sheet = resource.pixmap
    width, height = sheet.width(), sheet.height()
    if width == base_width and height == base_height:
        return [resource]
    sub_images = []
    for x in range(width//base_width):
        for y in range(height//base_height):
            region = sheet.copy(x*base_width, y*base_height, base_width, base_height)
            new_nid = resource.nid + " " + str(x) + ',' + str(y)
            new_image = Icon(new_nid, resource.full_path)
            new_image.icon_index = (x, y)
            new_image.parent_nid = resource.nid
            new_image.pixmap = region
            sub_images.append(new_image)
    return sub_images
