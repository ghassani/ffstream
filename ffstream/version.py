class Version:
	MAJOR = 1

	MINOR = 0

	PATCH = 0

	@staticmethod
	def version_major() -> int:
		return Version.MAJOR

	@staticmethod
	def version_minor() -> int:
		return Version.MINOR

	@staticmethod
	def version_patch() -> int:
		return Version.PATCH

	@staticmethod
	def version() -> str:
		return '%s.%s.%s' % (Version.MAJOR, Version.MINOR, Version.PATCH)