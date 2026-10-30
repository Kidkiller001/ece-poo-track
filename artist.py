from helper import slugify


class Artist:
    def __init__(self, name, bio, photo_url):
        self.name = name
        self.slug = slugify(name)
        self.bio = bio
        self.photo_url = photo_url

    def __eq__(self, other):
        if not isinstance(other, Artist):
            return NotImplemented
        return self.slug == other.slug

    def __hash__(self):
        return hash(self.slug)

    def to_dict(self):
        return {
            "slug": self.slug,
            "name": self.name,
            "bio": self.bio,
            "photo_url": self.photo_url,
        }
