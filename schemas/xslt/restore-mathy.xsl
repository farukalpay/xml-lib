<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <xsl:output method="html" version="5.0" encoding="UTF-8" indent="yes"/>

  <!-- Identity template - copy everything by default -->
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

  <!-- Transform op elements back to original names for display -->
  <xsl:template match="op[@xml:orig]">
    <span class="mathy-op" data-original="{@xml:orig}" data-uid="{@xml:uid}">
      <strong><xsl:value-of select="@xml:orig"/></strong>
      <xsl:apply-templates select="node()"/>
    </span>
  </xsl:template>

  <!-- Preserve op elements without xml:orig (shouldn't happen, but be safe) -->
  <xsl:template match="op[not(@xml:orig)]">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
