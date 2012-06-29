dist_noinst_SCRIPTS = xml2po.py

LANGS = ar bg ca cs da de el en en_GB es et fa fi fr fy he hr hu is it lt lv nl no pl pt ro ru sv sk sl sr th tr uk
LANGMO = $(LANGS:=.mo)
LANGPO = $(LANGS:=.po)

EXTRA_DIST = $(LANGPO)

if UPDATE_PO
# the TRANSLATORS: allows putting translation comments before the to-be-translated line.
oe-alliance-plugins-py.pot: $(top_srcdir)/*.py $(top_srcdir)/src/*/*.py $(top_srcdir)/src/*/*/*.py
	$(XGETTEXT) -L Python --from-code=UTF-8 --add-comments="TRANSLATORS:" -d @PACKAGE_NAME@ -s -o $@ $^

oe-alliance-plugins-xml.pot: $(srcdir)/xml2po.py $(top_srcdir)/src/*.xml $(top_srcdir)/src/*/*.xml $(top_srcdir)/src/*/*/*.xml
	$(PYTHON) $^ > $@

oe-alliance-plugins.pot: oe-alliance-plugins-py.pot oe-alliance-plugins-xml.pot
	cat $^ | $(MSGUNIQ) --no-location -o $@ -

%.po: oe-alliance-plugins.pot
	if [ -f $@ ]; then \
		$(MSGMERGE) --backup=none --no-location -s -N -U $@ $< && touch $@; \
	else \
		$(MSGINIT) -l $@ -o $@ -i $< --no-translator; \
	fi
endif

.po.mo:
	$(MSGFMT) -o $@ $<

BUILT_SOURCES = $(LANGMO)
CLEANFILES = $(LANGMO) oe-alliance-plugins-py.pot oe-alliance-plugins-xml.pot oe-alliance-plugins.pot

dist-hook: $(LANGPO)

install-data-local: $(LANGMO)
	for lang in $(LANGS); do \
		$(mkinstalldirs) $(DESTDIR)$(pkgdatadir)/po/$$lang/LC_MESSAGES; \
		$(INSTALL_DATA) $$lang.mo $(DESTDIR)$(pkgdatadir)/po/$$lang/LC_MESSAGES/@PACKAGE_NAME@.mo; \
	done

uninstall-local:
	for lang in $(LANGS); do \
		$(RM) $(DESTDIR)$(pkgdatadir)/po/$$lang/LC_MESSAGES/@PACKAGE_NAME@.mo; \
	done
