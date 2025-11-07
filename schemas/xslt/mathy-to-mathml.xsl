<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:m="http://www.w3.org/1998/Math/MathML"
    exclude-result-prefixes="xs">

  <xsl:output method="html" version="5.0" encoding="UTF-8" indent="yes"/>

  <!-- Identity template - copy everything by default -->
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

  <!-- Transform op elements to MathML -->
  <xsl:template match="op[@xml:orig]">
    <m:math xmlns:m="http://www.w3.org/1998/Math/MathML">
      <m:mrow>
        <m:mo><xsl:value-of select="@xml:orig"/></m:mo>
        <xsl:if test="node()">
          <m:mfenced>
            <xsl:apply-templates select="node()"/>
          </m:mfenced>
        </xsl:if>
      </m:mrow>
    </m:math>
  </xsl:template>

</xsl:stylesheet>
