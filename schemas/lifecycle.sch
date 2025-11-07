<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron"
            queryBinding="xslt2">

  <sch:title>XML Lifecycle Validation Rules</sch:title>

  <sch:ns prefix="xsl" uri="http://www.w3.org/1999/XSL/Transform"/>

  <!-- Surrogate element normalization: treat xml:orig as element name -->
  <sch:pattern id="surrogate-normalization">
    <sch:rule context="op[@xml:orig]">
      <sch:let name="original-name" value="@xml:orig"/>
      <sch:report test="true()" role="info">
        Surrogate element '<sch:value-of select="name()"/>' represents '<sch:value-of select="$original-name"/>'
      </sch:report>
    </sch:rule>
  </sch:pattern>

  <!-- Cross-file ID uniqueness -->
  <sch:pattern id="unique-ids">
    <sch:rule context="*[@id]">
      <sch:let name="id" value="@id"/>
      <sch:assert test="count(//*[@id = $id]) = 1">
        ID '<sch:value-of select="$id"/>' must be unique across all documents
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- Temporal monotonicity: timestamps must increase through lifecycle -->
  <sch:pattern id="temporal-order">
    <sch:rule context="document">
      <sch:let name="begin-time" value="phases/phase[@name='begin']/@timestamp"/>
      <sch:let name="start-time" value="phases/phase[@name='start']/@timestamp"/>
      <sch:let name="iteration-time" value="phases/phase[@name='iteration']/@timestamp"/>
      <sch:let name="end-time" value="phases/phase[@name='end']/@timestamp"/>
      <sch:let name="continuum-time" value="phases/phase[@name='continuum']/@timestamp"/>

      <sch:assert test="not($begin-time and $start-time) or $begin-time &lt;= $start-time">
        Begin timestamp must precede or equal Start timestamp
      </sch:assert>
      <sch:assert test="not($start-time and $iteration-time) or $start-time &lt;= $iteration-time">
        Start timestamp must precede or equal Iteration timestamp
      </sch:assert>
      <sch:assert test="not($iteration-time and $end-time) or $iteration-time &lt;= $end-time">
        Iteration timestamp must precede or equal End timestamp
      </sch:assert>
      <sch:assert test="not($end-time and $continuum-time) or $end-time &lt;= $continuum-time">
        End timestamp must precede or equal Continuum timestamp
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- Phase ordering: lifecycle phases must appear in canonical order -->
  <sch:pattern id="phase-order">
    <sch:rule context="phases">
      <sch:let name="phase-names" value="phase/@name"/>
      <sch:let name="begin-pos" value="index-of($phase-names, 'begin')"/>
      <sch:let name="start-pos" value="index-of($phase-names, 'start')"/>
      <sch:let name="iteration-pos" value="index-of($phase-names, 'iteration')"/>
      <sch:let name="end-pos" value="index-of($phase-names, 'end')"/>
      <sch:let name="continuum-pos" value="index-of($phase-names, 'continuum')"/>

      <sch:assert test="not($begin-pos and $start-pos) or $begin-pos[1] &lt; $start-pos[1]">
        Phase 'begin' must appear before 'start'
      </sch:assert>
      <sch:assert test="not($start-pos and $iteration-pos) or $start-pos[1] &lt; $iteration-pos[1]">
        Phase 'start' must appear before 'iteration'
      </sch:assert>
      <sch:assert test="not($iteration-pos and $end-pos) or $iteration-pos[last()] &lt; $end-pos[1]">
        Phase 'iteration' must appear before 'end'
      </sch:assert>
      <sch:assert test="not($end-pos and $continuum-pos) or $end-pos[1] &lt; $continuum-pos[1]">
        Phase 'end' must appear before 'continuum'
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- Reference integrity: refs must point to existing IDs -->
  <sch:pattern id="reference-integrity">
    <sch:rule context="*[@ref-begin]">
      <sch:let name="ref" value="@ref-begin"/>
      <sch:assert test="//begin[@id = $ref] or //phase[@name='begin'][@id = $ref]">
        Reference '<sch:value-of select="$ref"/>' must point to an existing begin phase
      </sch:assert>
    </sch:rule>

    <sch:rule context="*[@ref-start]">
      <sch:let name="ref" value="@ref-start"/>
      <sch:assert test="//start[@id = $ref] or //phase[@name='start'][@id = $ref]">
        Reference '<sch:value-of select="$ref"/>' must point to an existing start phase
      </sch:assert>
    </sch:rule>

    <sch:rule context="*[@ref-iteration]">
      <sch:let name="ref" value="@ref-iteration"/>
      <sch:assert test="//iteration[@id = $ref] or //phase[@name='iteration'][@id = $ref]">
        Reference '<sch:value-of select="$ref"/>' must point to an existing iteration phase
      </sch:assert>
    </sch:rule>

    <sch:rule context="*[@ref-end]">
      <sch:let name="ref" value="@ref-end"/>
      <sch:assert test="//end[@id = $ref] or //phase[@name='end'][@id = $ref]">
        Reference '<sch:value-of select="$ref"/>' must point to an existing end phase
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- Checksum validation: if present, must be valid format -->
  <sch:pattern id="checksum-format">
    <sch:rule context="*[@checksum]">
      <sch:assert test="matches(@checksum, '^[a-f0-9]{64}$')">
        Checksum must be a valid SHA-256 hash (64 hex characters)
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- Iteration cycles must be sequential -->
  <sch:pattern id="iteration-cycles">
    <sch:rule context="iteration[@cycle]">
      <sch:let name="cycle" value="@cycle"/>
      <sch:assert test="$cycle >= 1">
        Iteration cycle must be >= 1
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- Document must have at least begin phase -->
  <sch:pattern id="minimum-phases">
    <sch:rule context="document/phases">
      <sch:assert test="phase[@name='begin']">
        Document must contain at least a 'begin' phase
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- Path references must exist (warning) -->
  <sch:pattern id="path-references">
    <sch:rule context="phase/use[@path]">
      <sch:report test="true()" role="warning">
        Path reference: <sch:value-of select="@path"/> (verify file exists)
      </sch:report>
    </sch:rule>
    <sch:rule context="reference[@path]">
      <sch:report test="true()" role="warning">
        Path reference: <sch:value-of select="@path"/> (verify file exists)
      </sch:report>
    </sch:rule>
  </sch:pattern>

</sch:schema>
