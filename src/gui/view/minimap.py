import cv2
import tkinter as tk
from PIL import ImageTk, Image
from src.gui.interfaces import LabelFrame
from src.common import bot_status, utils, bot_settings
from src.routine.components import Point
from src.modules.capture import capture
from src.routine.routine import routine


class Minimap(LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'Minimap', **kwargs)

        self.WIDTH = 400
        self.HEIGHT = 300
        self.canvas = tk.Canvas(self, bg='black',
                                width=self.WIDTH, height=self.HEIGHT,
                                borderwidth=0, highlightthickness=0)
        self.canvas.pack(expand=True, fill='both', padx=5, pady=5)
        self.container = None

    def display_minimap(self):
        """Updates the Main page with the current minimap."""

        minimap = capture.minimap_display
        if minimap is not None:
            rune_pos = capture.point_2_minimap(bot_status.rune_pos)
            minal_pos = capture.point_2_minimap(bot_status.minal_pos)
            path = [capture.point_2_minimap(p) for p in bot_status.path]
            player_pos = capture.point_2_minimap(bot_status.player_pos)
            minimap_img = minimap
            
            height, width, _ = minimap_img.shape
            if width == 0 or height == 0:
                return
            
            img = cv2.cvtColor(minimap_img, cv2.COLOR_BGR2RGB)

            # Resize minimap to fit the Canvas
            ratio = min(self.WIDTH / width, self.HEIGHT / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            if new_height * new_width > 0:
                img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)

            # Mark the position of the active rune
            if rune_pos:
                cv2.circle(img,
                           utils.trans_point(rune_pos, ratio),
                           3,
                           (128, 0, 128),
                           1)

            if minal_pos:
                cv2.circle(img,
                           utils.trans_point(bot_status.minal_pos, ratio),
                           3,
                           (255, 0, 0),
                           1)

            # Draw the current path that the program is taking
            if bot_status.enabled and len(path) > 1:
                for i in range(len(path) - 1):
                    start = utils.trans_point(path[i], ratio)
                    end = utils.trans_point(path[i + 1], ratio)
                    cv2.line(img, start, end, (0, 255, 255), 1)

            # Draw each Point in the routine as a circle
            for p in routine.sequence:
                if isinstance(p, Point):
                    utils.draw_location(img,
                                        capture.point_2_minimap(p.location),
                                        ratio,
                                        (0, 255, 0) if bot_status.enabled else (255, 0, 0),
                                        p.tolerance)

            # Display the current Layout
            # if layout:
            #     layout.draw(img)

            # Draw the player's position on top of everything
            cv2.circle(img,
                       utils.trans_point(player_pos, ratio),
                       3,
                       (255, 0, 0),
                       -1)

            # Display the minimap in the Canvas
            img = ImageTk.PhotoImage(Image.fromarray(img))
            if self.container is None:
                self.container = self.canvas.create_image(self.WIDTH // 2,
                                                          self.HEIGHT // 2,
                                                          image=img, anchor=tk.CENTER)
            else:
                self.canvas.itemconfig(self.container, image=img)
            self._img = img                 # Prevent garbage collection