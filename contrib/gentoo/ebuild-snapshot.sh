#!/usr/bin/env bash

# ebuild-snapshot.sh 
#
#   <dmeyer@tzi.de>
# $Id$


version=`echo $1 | sed 's/-bla/_/g' | sed 's/-r[0-9]//'`
ebuild_version=`echo $1 | sed 's/-/_/g' | sed 's/_\(r[0-9]\)/-\1/'`
tag=REL-`echo $1 | sed 's/\./_/g' | sed 'y/prerc/PRERC/'` 
echo src name: freevo-$ebuild_version and freevo-src-$version
echo ebuild: freevo-$ebuild_version
echo cvs tag:  $tag

read

cd `dirname $0`/../../

function cvs_update {
    echo cvs update
    cvs update -dP
}

function cvs_tag {
    echo setting new cvs tag
    cvs tag $tag
}

function cleanup_and_pack {
    echo cleaning up
    cd /tmp/freevo-$version
    rm freevo.conf* local_conf.py local_skin.fxd
    find /tmp/freevo-$version -type d -name CVS | xargs rm -rf
    find /tmp/freevo-$version -name .cvsignore  | xargs rm -rf
    find /tmp/freevo-$version -name '.#*'       | xargs rm -rf
    find /tmp/freevo-$version -name '*.pyo'     | xargs rm -rf
    find /tmp/freevo-$version -name '*.pyc'     | xargs rm -rf
    rm -rf find /tmp/freevo-$version/WIP /tmp/freevo-$version/dischi1 \
	/tmp/freevo-$version/aubin1 /tmp/freevo-$version/contrib/gentoo

    ./autogen.sh
    rm ./autogen.sh
    sudo chown -R root.root /tmp/freevo-$version

    cd /tmp/
    echo making tgz
    sudo tar -zcvf /usr/portage/distfiles/freevo-src-$version.tgz freevo-$version

    echo remove tmp dir
    sudo rm -rf freevo-$version
}

function pack {
    cd ..
    sudo rm -rf /tmp/freevo-$version
    echo copy directory to /tmp
    cp -r freevo /tmp/freevo-$version
    cp -r  ~/src/wiki/freevo.sourceforge.net/cgi-bin/moin.cgi/ /tmp/freevo-$version/Docs/html
    cleanup_and_pack
}

function pack_tag {
    cd /tmp
    sudo rm -rf freevo-$version
    mkdir freevo-$version
    cd freevo-$version
    cp -r /home/dmeyer/src/freevo/CVS .
    cvs update -r $tag -dP
    cleanup_and_pack
}

function ebuild {
    sudo cp /home/dmeyer/src/freevo/contrib/gentoo/freevo.ebuild \
	/usr/local/portage/media-video/freevo/freevo-$ebuild_version.ebuild
    cd /usr/local/portage/media-video/freevo
    sudo rm -f files/digest-freevo-$version
    sudo chown -R root.root .
    sudo ebuild freevo-$ebuild_version.ebuild digest 
}

function ebuild_upload {
    sudo rm -rf /tmp/ebuild*
    (
	cd /usr/local/portage

	tar --atime-preserve -zcvf /tmp/freevo-ebuild.tgz \
	    media-tv/freevo media-tv/freevo-snapshot dev-python/mmpython-snapshot \
	    media-video/xine-ui media-libs/libsdl >/dev/null
    )
    scp -r contrib/gentoo/ChangeLog contrib/gentoo/rsync-freevo /tmp/freevo-ebuild.tgz \
	dischi@freevo.sf.net:/home/groups/f/fr/freevo/htdocs/gentoo
    rm /tmp/freevo-ebuild.tgz
}

function sf_upload {
    # not working
    cd /usr/portage/distfiles/
    curl -T freevo-src-$version.tgz \
	ftp://anonymous:dmeyer_tzi.de@upload.sourceforge.net/incoming
}

function get_wiki {
    httrack -O wiki http://freevo.sourceforge.net/cgi-bin/moin.cgi/ \
	"-*action=*" "-*UserPref*" "-*FindPage*" "-*HelpContents*" \
	"-*FreevoWikiHelp*" "-*RecentChanges*" "-*TitleIndex*" \
	"-*WordIndex*" "-*SiteNavigation*" "-*Hilfe*" "-*HelpOn*" \
	"-*AbandonedPages.html*" "-*Aktuelle_c4nderungen.html*" \
	"-*AufgegebeneSeiten.html*" "-*BenutzerEinstellungen.html*"
}

eval $2


# end of ebuild-snapshot.sh 
