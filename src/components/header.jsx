import React from 'react';
import { Link } from 'gatsby';
import { AVATAR, NAVS } from '../utils/const';

const Header = ({ siteTitle }) => {
  if (!AVATAR && !NAVS) return null;
  return (
    <>
      <nav
        className="db flex justify-between w-100 ph5-l"
        style={{ marginTop: '3rem' }}
      >
        {AVATAR && (
          <div className="dib w-25 v-mid">
            <Link to="/" className="link dim">
              <picture>
                <img
                  className="dib w3 h3 br-100"
                  alt={siteTitle || 'avatar'}
                  src={AVATAR}
                />
              </picture>
            </Link>
          </div>
        )}
        {NAVS && (
          <div className="dib w-75 v-mid tr">
            {NAVS.map((n) => (
              <a
                href={n.link}
                className="light-gray link dim f6 f5-l mr3 mr4-l"
              >
                {n.text}
              </a>
            ))}
          </div>
        )}
      </nav>
    </>
  );
};

export default Header;
