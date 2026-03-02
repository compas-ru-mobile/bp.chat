

class CssClassControl:

    def __init__(self):
        self.d = {}

    def add(self, obj, class_name):
        if class_name in self.d:
            self.d[class_name].add(obj)
        else:
            self.d[class_name] = {obj,}

    def update_style(self, cls_dict):
        for class_name, lst in self.d.items():
            cls_css = cls_dict.get(class_name, None)
            if cls_css is not None:
                for obj in lst:
                    obj.setStyleSheet(cls_css)

cssClassControl = CssClassControl()
