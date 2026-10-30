from helper import slugify


class Artist:
    def __init__(self, name, bio, photo_url):
        self.name = name
        self.slug = slugify(name)
        self.bio = bio
        self.photo_url = photo_url

    def to_dict(self):
        return {
            "slug": self.slug,
            "name": self.name,
            "bio": self.bio,
            "photo_url": self.photo_url,
        }