import React, { useCallback, useEffect, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import PageContent from 'Components/Page/PageContent';
import PageContentBody from 'Components/Page/PageContentBody';
import { inputTypes, kinds } from 'Helpers/Props';
import themes from 'Styles/Themes';
import translate from 'Utilities/String/translate';

const SECTION = 'ui';




export const timeFormatOptions = [
  { key: 'h(:mm)a', value: '5pm/5:30pm' },
  { key: 'HH:mm', value: '17:00/17:30' },
];

function UISettings() {


  return (
    <PageContent title={translate('UiSettings')}>

      <PageContentBody>
        <div> UI Content</div>
      </PageContentBody>
    </PageContent>
  );
}

export default UISettings;