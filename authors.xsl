<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="text" encoding="UTF-8"/>
  <xsl:template match="text()"/>
  <xsl:template match="author">
    <xsl:value-of select="normalize-space(.)"/><xsl:text>&#xA;</xsl:text>
  </xsl:template>
</xsl:stylesheet>
